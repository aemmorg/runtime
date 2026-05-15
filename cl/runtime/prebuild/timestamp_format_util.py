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
from cl.runtime.primitive.crockford_util import CrockfordUtil

_TEXT_EXTENSIONS = (".py", ".csv", ".yaml", ".yml", ".json", ".jsonl", ".txt")
"""File extensions treated as text files for timestamp format checking."""

_ISO_DELIMITED_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\.(\d{3})Z-([a-fA-F0-9]{20})")
"""Regex for the ISO-delimited legacy format: yyyy-MM-ddThh:mm:ss.fffZ-hex(20)."""

_LEGACY_DASH_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{3})-([a-fA-F0-9]{20})")
"""Regex for the dash-delimited legacy format: yyyy-MM-dd-hh-mm-ss-fff-hex(20)."""


class TimestampFormatUtil:
    """Helper class for checking and fixing legacy timestamp formats."""

    @classmethod
    def _convert_match(cls, match: re.Match) -> str:
        """Convert a legacy timestamp match to YYYYMMDD-HHMMSSFFF-CROCKFORD16 format."""
        yyyy, mm, dd, hh, mi, ss, fff, hex20 = match.groups()
        crockford = CrockfordUtil.encode(int(hex20, 16), 16)
        return f"{yyyy}{mm}{dd}-{hh}{mi}{ss}{fff}-{crockford}"

    @classmethod
    def check_or_fix_text(cls, text: str, *, fix: bool) -> tuple[str, int]:
        """Check or fix legacy timestamps in text.

        Args:
            text: Text content to check or fix
            fix: If True, replace legacy timestamps with the new format

        Returns:
            Tuple of (text, count) where count is the number of legacy timestamps found.
            If fix is True, text contains the updated content; otherwise the original text is returned.
        """
        iso_count = len(_ISO_DELIMITED_RE.findall(text))
        dash_count = len(_LEGACY_DASH_RE.findall(text))
        count = iso_count + dash_count

        if fix and count > 0:
            text = _ISO_DELIMITED_RE.sub(cls._convert_match, text)
            text = _LEGACY_DASH_RE.sub(cls._convert_match, text)

        return text, count

    @classmethod
    def check_or_fix_file(cls, file_path: str, *, fix: bool) -> bool:
        """Check or fix legacy timestamps in a single file.

        Args:
            file_path: Path to the file to check or fix
            fix: If True, replace legacy timestamps with the new format

        Returns:
            True if the file has no legacy timestamps (valid), False otherwise.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            return True

        new_content, count = cls.check_or_fix_text(content, fix=fix)

        if fix and count > 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

        return count == 0

    @classmethod
    def check_or_fix_format(
        cls,
        *,
        dirs: Sequence[str],
        fix: bool,
        verbose: bool = False,
        file_exclude_patterns: Sequence[str] | None = None,
        dir_exclude_patterns: Sequence[str] | None = None,
    ) -> None:
        """Check or fix legacy timestamp formats in all text files under the given directories.

        Args:
            dirs: Directories where file search is performed
            fix: If True, fix all legacy timestamps; if False, only check and report
            verbose: Print messages about fixes to stdout if specified
            file_exclude_patterns: Optional list of filename glob patterns to exclude
            dir_exclude_patterns: Optional list of directory name glob patterns to exclude
        """
        if file_exclude_patterns is None:
            file_exclude_patterns = []
        if dir_exclude_patterns is None:
            dir_exclude_patterns = []

        total_files_changed = 0
        total_replacements = 0
        files_with_errors = []

        for dir_path in dirs:
            if not os.path.isdir(dir_path):
                continue
            for root, dirnames, filenames in os.walk(dir_path):
                # Skip hidden, special, and explicitly excluded directories
                dirnames[:] = [
                    d
                    for d in dirnames
                    if not d.startswith(".")
                    and not d.startswith("__")
                    and d != "logs"
                    and not any(fnmatch(d, pat) for pat in dir_exclude_patterns)
                ]

                for filename in filenames:
                    if not any(filename.endswith(ext) for ext in _TEXT_EXTENSIONS):
                        continue
                    if any(fnmatch(filename, pat) for pat in file_exclude_patterns):
                        continue

                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                    except (UnicodeDecodeError, PermissionError):
                        continue

                    new_content, count = cls.check_or_fix_text(content, fix=fix)
                    if count > 0:
                        if fix:
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(new_content)
                            if verbose:
                                print(f"  {file_path}: {count} timestamp(s) converted")
                            total_files_changed += 1
                            total_replacements += count
                        else:
                            files_with_errors.append(file_path)

        if fix and verbose:
            print(f"\nDone: {total_replacements} timestamp(s) converted in {total_files_changed} file(s)")

        if not fix and files_with_errors:
            raise RuntimeError(
                f"Legacy timestamp format found in {len(files_with_errors)} file(s):\n"
                + "".join(f"    {f}\n" for f in files_with_errors)
            )
