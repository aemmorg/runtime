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

import os
import re
from fnmatch import fnmatch
from typing import Sequence
from cl.runtime.primitive.string_util import StringUtil
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.settings.package_settings import PackageSettings

_LICENSE_MD5_TO_NAME = {
    "f9154a63c383844813d6abf79e4230d1": "Apache Software License",
    "124c1fc0f9f45eeba2cdd9a556e61eb2": "LicenseRef-Proprietary",
}
"""Mapping from StringUtil.md5_hex of LICENSE file contents to license name."""

_COPYRIGHT_AUTHOR_RE = re.compile(r"Copyright\s+\(C\)\s+\d{4}-present\s+(.+?)(?:\.\s*All rights reserved\.)?$")
"""Regex to extract author name from the first line of a COPYRIGHT file."""


class CopyrightUtil:
    """Helper class for working with copyright headers and files."""

    @classmethod
    def read_copyright_header(cls, package_root: str) -> str:
        """Read COPYRIGHT file at package root and convert to Python comment header preceded by '# '.

        Args:
            package_root: Absolute path to the package root directory
        """
        copyright_file_path = os.path.join(package_root, "COPYRIGHT")
        with open(copyright_file_path, "r", encoding="utf-8") as f:
            copyright_text = f.read().rstrip("\n")
        lines = copyright_text.split("\n")
        header_lines = [("# " + line).rstrip() for line in lines]
        return "\n".join(header_lines) + "\n"

    @classmethod
    def get_authors(cls, package_root: str, package_namespace: str) -> str:
        """Extract author name from the COPYRIGHT file at package root.

        Args:
            package_root: Absolute path to the package root directory
            package_namespace: Package namespace for error messages (e.g., 'cl.runtime')
        """
        copyright_file_path = os.path.join(package_root, "COPYRIGHT")
        with open(copyright_file_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        match = _COPYRIGHT_AUTHOR_RE.match(first_line)
        if not match:
            raise RuntimeError(
                f"Unable to obtain authors from COPYRIGHT file for {package_namespace}, "
                f"specify package_authors field in cl.{package_namespace.split('.')[-1]}.settings.yaml"
            )
        return match.group(1).strip()

    @classmethod
    def get_license_name(cls, package_root: str, package_namespace: str) -> str:
        """Determine license name from the LICENSE file at package root using MD5 lookup.

        Args:
            package_root: Absolute path to the package root directory
            package_namespace: Package namespace for error messages (e.g., 'cl.runtime')
        """
        license_file_path = os.path.join(package_root, "LICENSE")
        with open(license_file_path, "r", encoding="utf-8") as f:
            license_text = f.read()
        license_md5 = StringUtil.md5_hex(license_text)
        license_name = _LICENSE_MD5_TO_NAME.get(license_md5)
        if license_name is None:
            raise RuntimeError(
                f"Unable to obtain license name from LICENSE file for {package_namespace} (md5={license_md5}), "
                f"specify package_license field in cl.{package_namespace.split('.')[-1]}.settings.yaml"
            )
        return license_name

    @classmethod
    def _get_source_files(
        cls,
        *,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> list[tuple[str, str]]:
        """Get list of (copyright_header, file_path) tuples for all source files.

        Args:
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude

        Returns:
            List of tuples (copyright_header, file_path) for all matched source files.
        """

        if file_include_patterns is None:
            file_include_patterns = ["*.py"]
        if file_exclude_patterns is None:
            file_exclude_patterns = ["__init__.py", "_version.py"]

        packages = PackageSettings.instance().get_packages()
        result = []
        all_root_paths = set()

        for package in packages:
            package_root = ProjectLayout.get_package_root(package)
            copyright_header = cls.read_copyright_header(package_root)

            # Add paths to source, stubs, and test directories
            package_root_paths = []
            if (x := ProjectLayout.get_package_source_root(package)) is not None and x not in all_root_paths:
                package_root_paths.append(x)
                all_root_paths.add(x)
            if (x := ProjectLayout.get_package_stubs_root(package)) is not None and x not in all_root_paths:
                package_root_paths.append(x)
                all_root_paths.add(x)
            if (x := ProjectLayout.get_package_tests_root(package)) is not None and x not in all_root_paths:
                package_root_paths.append(x)
                all_root_paths.add(x)

            if not package_root_paths:
                continue

            for root_path in package_root_paths:
                for dir_path, dir_names, filenames in os.walk(root_path):
                    filenames = [x for x in filenames if any(fnmatch(x, y) for y in file_include_patterns)]
                    filenames = [x for x in filenames if not any(fnmatch(x, y) for y in file_exclude_patterns)]
                    for filename in filenames:
                        file_path = os.path.join(dir_path, filename)
                        result.append((copyright_header, str(file_path)))

        return result

    @classmethod
    def _read_file_header(cls, content: str) -> str:
        """Extract the comment block at the top of a file (consecutive lines starting with '#').

        Args:
            content: Full file content

        Returns:
            The comment block including a trailing newline, or empty string if no comment block found.
        """
        lines = content.split("\n")
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith("#"):
                header_end = i + 1
            else:
                break
        if header_end == 0:
            return ""
        return "\n".join(lines[:header_end]) + "\n"

    @classmethod
    def fix_copyright_headers(
        cls,
        *,
        verbose: bool = False,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> None:
        """Fix copyright headers and trailing blank lines in all source files.

        Replaces incorrect or missing copyright headers with the correct header from the COPYRIGHT
        file and ensures a blank line follows the header.

        Args:
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        source_files = cls._get_source_files(
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        fixed_header_files = []
        fixed_blank_line_files = []

        for copyright_header, file_path in source_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if content.startswith(copyright_header):
                # Correct header, check trailing blank line
                after_header = content[len(copyright_header):]
                if after_header and not after_header.startswith("\n"):
                    content = copyright_header + "\n" + after_header
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    fixed_blank_line_files.append(file_path)
            else:
                # Wrong or missing header - find end of existing comment block and replace
                lines = content.split("\n")
                header_end = 0
                for i, line in enumerate(lines):
                    if line.startswith("#"):
                        header_end = i + 1
                    else:
                        break

                remaining = "\n".join(lines[header_end:])
                if remaining and not remaining.startswith("\n"):
                    content = copyright_header + "\n" + remaining
                else:
                    content = copyright_header + remaining

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_header_files.append(file_path)

        if verbose:
            if fixed_header_files:
                print(
                    f"Fixed copyright header in {len(fixed_header_files)} file(s):\n"
                    + "".join(f"    {f}\n" for f in fixed_header_files)
                )
            if fixed_blank_line_files:
                print(
                    f"Fixed missing blank line after copyright header in {len(fixed_blank_line_files)} file(s):\n"
                    + "".join(f"    {f}\n" for f in fixed_blank_line_files)
                )
            if not fixed_header_files and not fixed_blank_line_files:
                print("All copyright headers and trailing blank lines are correct.")

    @classmethod
    def test_copyright_headers(
        cls,
        *,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> None:
        """Test that copyright headers are correct and followed by a blank line in all source files.

        Raises RuntimeError with a detailed message listing files with errors, the expected header,
        and each unique non-matching header found.

        Args:
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        source_files = cls._get_source_files(
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        # Group header mismatch errors by expected copyright header
        # key: expected header, value: list of file paths
        header_error_files: dict[str, list[str]] = {}
        # key: expected header, value: set of unique non-matching headers found
        wrong_headers_found: dict[str, set[str]] = {}
        # Files where correct header is present but trailing blank line is missing
        blank_line_error_files: list[str] = []

        for copyright_header, file_path in source_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if content.startswith(copyright_header):
                # Correct header, check trailing blank line
                after_header = content[len(copyright_header):]
                if after_header and not after_header.startswith("\n"):
                    blank_line_error_files.append(file_path)
            else:
                # Wrong or missing header
                header_error_files.setdefault(copyright_header, []).append(file_path)
                actual_header = cls._read_file_header(content)
                wrong_headers_found.setdefault(copyright_header, set()).add(actual_header)

        # Build detailed error message
        error_parts = []

        for expected_header, files in header_error_files.items():
            part = (
                f"Copyright header does not match in {len(files)} file(s):\n"
                + "".join(f"    {f}\n" for f in files)
                + "\nExpected copyright header (from COPYRIGHT at package root):\n"
                + "".join(f"    {line}\n" for line in expected_header.rstrip("\n").split("\n"))
            )
            unique_headers = wrong_headers_found.get(expected_header, set())
            if unique_headers:
                part += "\nNon-matching header(s) found:\n"
                for i, header in enumerate(sorted(unique_headers)):
                    if i > 0:
                        part += "\n"
                    if header:
                        part += "".join(f"    {line}\n" for line in header.rstrip("\n").split("\n"))
                    else:
                        part += "    (no copyright header found)\n"
            error_parts.append(part)

        if blank_line_error_files:
            error_parts.append(
                f"Blank line after copyright header is missing in {len(blank_line_error_files)} file(s):\n"
                + "".join(f"    {f}\n" for f in blank_line_error_files)
            )

        if error_parts:
            raise RuntimeError("\n".join(error_parts))
