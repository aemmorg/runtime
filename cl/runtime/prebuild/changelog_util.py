# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
import re
import subprocess
from pathlib import Path
from cl.runtime.project.project_util import ProjectUtil
from cl.runtime.settings.package_settings import PackageSettings


class ChangelogUtil:
    """Helper class for generating and updating CHANGELOG.md files from git history."""

    _CHANGELOG_FILENAME = "CHANGELOG.md"
    """Standard changelog filename."""

    _DATE_HEADER_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})")
    """Regex to match date section headers like '## 2026-02-21'."""

    @classmethod
    def get_yesterday_utc(cls) -> datetime.date:
        """Get yesterday's date in UTC."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return (now - datetime.timedelta(days=1)).date()

    @classmethod
    def get_changelog_path(cls, *, package: str) -> str:
        """Get the absolute path to the CHANGELOG.md for the specified package.

        Args:
            package: Dot-delimited package namespace, e.g., 'cl.runtime'

        Returns:
            Absolute path to the package's CHANGELOG.md file.
        """
        package_root = ProjectUtil.get_package_root(package)
        return os.path.join(package_root, cls._CHANGELOG_FILENAME)

    @classmethod
    def get_last_changelog_date(cls, *, changelog_path: str) -> datetime.date | None:
        """Parse an existing CHANGELOG.md to find the most recent date entry.

        Args:
            changelog_path: Absolute path to the CHANGELOG.md file

        Returns:
            The most recent date found in the changelog, or None if no changelog
            exists or no date entries are found.
        """
        if not os.path.exists(changelog_path):
            return None

        with open(changelog_path, "r", encoding="utf-8") as f:
            for line in f:
                match = cls._DATE_HEADER_RE.match(line.strip())
                if match:
                    return datetime.date.fromisoformat(match.group(1))

        return None

    @classmethod
    def get_git_log(
        cls,
        *,
        since_date: datetime.date | None = None,
        until_date: datetime.date,
        path_filter: str | None = None,
    ) -> list[tuple[datetime.date, str]]:
        """Get git log entries between dates, optionally filtered by path.

        Args:
            since_date: Start date (exclusive). If None, only until_date is collected.
            until_date: End date (inclusive). Typically yesterday UTC.
            path_filter: Optional directory path to filter commits by.

        Returns:
            List of (date, subject) tuples.
        """
        project_root = ProjectUtil.get_project_root()

        cmd = [
            "git",
            "log",
            "--all",
            "--format=%ai|%s",
            f"--before={until_date + datetime.timedelta(days=1)}",
        ]

        if since_date is not None:
            cmd.append(f"--after={since_date}")

        if path_filter is not None:
            cmd.extend(["--", path_filter])

        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"git log command failed with return code {result.returncode}.\n" f"stderr: {result.stderr}"
            )

        entries = []
        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            parts = line.split("|", 1)
            if len(parts) != 2:
                continue
            date_str = parts[0].strip().split(" ")[0]
            subject = parts[1].strip()
            commit_date = datetime.date.fromisoformat(date_str)
            # Post-filter to enforce strict date boundaries (since_date < date <= until_date)
            # because git --after includes commits on the boundary date
            if since_date is not None and commit_date <= since_date:
                continue
            if commit_date > until_date:
                continue
            entries.append((commit_date, subject))

        return entries

    @classmethod
    def group_entries_by_date(
        cls,
        entries: list[tuple[datetime.date, str]],
    ) -> list[tuple[datetime.date, list[str]]]:
        """Group commit entries by date, sorted most recent first.

        Deduplicates commit messages within each date group.

        Args:
            entries: List of (date, subject) tuples from get_git_log.

        Returns:
            List of (date, subjects) tuples sorted by date descending.
        """
        date_to_subjects: dict[datetime.date, list[str]] = {}
        for commit_date, subject in entries:
            date_to_subjects.setdefault(commit_date, []).append(subject)

        result = []
        for d in sorted(date_to_subjects.keys(), reverse=True):
            seen = set()
            unique_subjects = []
            for s in date_to_subjects[d]:
                if s not in seen:
                    seen.add(s)
                    unique_subjects.append(s)
            unique_subjects.sort()
            result.append((d, unique_subjects))

        return result

    @classmethod
    def format_changelog(
        cls,
        *,
        package: str,
        grouped_entries: list[tuple[datetime.date, list[str]]],
        existing_content: str | None = None,
    ) -> str:
        """Format changelog entries into Keep a Changelog format.

        If existing_content is provided, prepends new entries after the header.
        Otherwise creates a complete new CHANGELOG.md.

        Args:
            package: Dot-delimited package namespace for the header, e.g., 'cl.runtime'
            grouped_entries: Output from group_entries_by_date.
            existing_content: Existing CHANGELOG.md content to merge with, or None.

        Returns:
            Complete CHANGELOG.md content as a string.
        """
        header = f"# Changelog for {package}\n\n"
        header += "All notable changes to this package will be documented in this file.\n\n"
        header += "The format is based on [Keep a Changelog](https://keepachangelog.com).\n\n"

        new_section_lines = []
        for commit_date, subjects in grouped_entries:
            new_section_lines.append(f"## {commit_date.isoformat()}\n\n")
            for subject in subjects:
                new_section_lines.append(f"- {subject}\n")
            new_section_lines.append("\n")

        new_sections = "".join(new_section_lines)

        if existing_content is None:
            return header + new_sections
        else:
            lines = existing_content.split("\n")
            header_end_index = len(lines)
            for i, line in enumerate(lines):
                if cls._DATE_HEADER_RE.match(line):
                    header_end_index = i
                    break

            existing_header = "\n".join(lines[:header_end_index])
            if not existing_header.endswith("\n"):
                existing_header += "\n"
            if not existing_header.endswith("\n\n"):
                existing_header += "\n"
            existing_entries = "\n".join(lines[header_end_index:])

            return existing_header + new_sections + existing_entries

    @classmethod
    def update_package_changelog(cls, *, package: str) -> str:
        """Update the CHANGELOG.md for a single package.

        On first run (no existing CHANGELOG.md), collects only yesterday's commits.
        On subsequent runs, collects from the day after the last entry to yesterday UTC.

        Args:
            package: Dot-delimited package namespace, e.g., 'cl.runtime'

        Returns:
            Path to the updated CHANGELOG.md file, or a message if no new entries.
        """
        changelog_path = cls.get_changelog_path(package=package)
        yesterday = cls.get_yesterday_utc()

        last_date = cls.get_last_changelog_date(changelog_path=changelog_path)

        if last_date is None:
            # First run: only collect yesterday
            since_date = yesterday - datetime.timedelta(days=1)
        else:
            since_date = last_date

        package_settings = PackageSettings.instance()
        package_dir = package_settings.package_dirs.get(package)
        if package_dir is None:
            raise RuntimeError(f"Package {package} is not listed in settings.yaml 'package_dirs' field.")

        entries = cls.get_git_log(
            since_date=since_date,
            until_date=yesterday,
            path_filter=package_dir,
        )

        if not entries:
            return f"No new commits for {package} since {last_date or yesterday}"

        grouped = cls.group_entries_by_date(entries)

        existing_content = None
        if os.path.exists(changelog_path):
            with open(changelog_path, "r", encoding="utf-8") as f:
                existing_content = f.read()

        content = cls.format_changelog(
            package=package,
            grouped_entries=grouped,
            existing_content=existing_content,
        )

        Path(changelog_path).parent.mkdir(parents=True, exist_ok=True)
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write(content)

        return changelog_path

    @classmethod
    def update_project_changelogs(cls) -> list[str]:
        """Update CHANGELOG.md for all main packages in the project.

        Returns:
            List of result messages (paths to updated files or no-new-commits messages).
        """
        all_packages = PackageSettings.instance().get_packages()
        results = []
        for package in all_packages:
            if package.startswith("stubs."):
                continue
            result = cls.update_package_changelog(package=package)
            results.append(result)
        return results
