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

import subprocess
import sys
from typing import Sequence
from cl.runtime.prebuild.source_util import SourceUtil

_MAX_CMD_BATCH = 200
"""Maximum number of file paths per ruff invocation to stay within command-line length limits."""

_RUFF_SELECT = ["D"]
"""Ruff rule selector for all pydocstyle checks."""

_RUFF_IGNORE = [
    "D100", "D101", "D102", "D103", "D104", "D105", "D106", "D107",
    "D200", "D202", "D203", "D205", "D212", "D213",
    "D301",
    "D400", "D401", "D402", "D403", "D404",
    "D410", "D411", "D413", "D415", "D417",
]
"""Ruff pydocstyle rules to ignore (remove from this list as violations are fixed)."""


class DocstringUtil:
    """Helper class for detecting and fixing docstring formatting issues using ruff pydocstyle rules."""

    @classmethod
    def _run_ruff_docstring_check(
        cls,
        file_paths: list[str],
        *,
        fix: bool = False,
        extra_ignore_rules: Sequence[str] | None = None,
    ) -> tuple[int, str, str]:
        """Run ruff pydocstyle checks on the given files, optionally applying fixes.

        Args:
            file_paths: List of absolute file paths to check
            fix: If True, apply fixes in place
            extra_ignore_rules: Optional list of additional ruff rule codes to ignore (e.g. ["D202"])

        Returns:
            Tuple of (total_violation_count, combined_stdout, combined_stderr).

        """
        total_violations = 0
        all_stdout = []
        all_stderr = []

        select_arg = ",".join(_RUFF_SELECT)
        ignore_rules = list(_RUFF_IGNORE)
        if extra_ignore_rules:
            ignore_rules.extend(extra_ignore_rules)
        ignore_arg = ",".join(ignore_rules)

        for i in range(0, len(file_paths), _MAX_CMD_BATCH):
            batch = file_paths[i : i + _MAX_CMD_BATCH]
            cmd = [sys.executable, "-m", "ruff", "check", "--select", select_arg, "--ignore", ignore_arg]
            if fix:
                cmd.extend(["--fix", "--unsafe-fixes"])
            cmd.extend(batch)
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.stdout:
                all_stdout.append(result.stdout)
            if result.stderr:
                all_stderr.append(result.stderr)
            # Count violations from output lines matching the D-rule pattern
            for line in result.stdout.splitlines():
                if ": D" in line and " [" in line:
                    total_violations += 1

        return total_violations, "\n".join(all_stdout), "\n".join(all_stderr)

    @classmethod
    def validate_docstrings(
        cls,
        *,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
        extra_ignore_rules: Sequence[str] | None = None,
    ) -> None:
        """Test that docstrings comply with pydocstyle formatting rules.

        Raises RuntimeError with a list of violations if any are found.

        Args:
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
            extra_ignore_rules: Optional list of additional ruff rule codes to ignore on top of the
                default ignore list (e.g. ["D202"] to skip the no-blank-line-after-docstring check)

        """
        if file_exclude_patterns is None:
            file_exclude_patterns = ["stub_invalid_docstring*"]

        source_files = SourceUtil.get_abs_source_files(
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        if not source_files:
            return

        violation_count, stdout, stderr = cls._run_ruff_docstring_check(
            source_files, fix=False, extra_ignore_rules=extra_ignore_rules,
        )

        if violation_count > 0:
            raise RuntimeError(
                f"Docstring formatting violations (pydocstyle D rules) "
                f"in {violation_count} location(s):\n{stdout}"
            )

    @classmethod
    def fix_docstrings(
        cls,
        *,
        verbose: bool = False,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
        extra_ignore_rules: Sequence[str] | None = None,
    ) -> None:
        """Fix auto-fixable docstring formatting issues using ruff pydocstyle rules.

        Args:
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
            extra_ignore_rules: Optional list of additional ruff rule codes to ignore on top of the
                default ignore list (e.g. ["D202"] to skip the no-blank-line-after-docstring check)

        """
        if file_exclude_patterns is None:
            file_exclude_patterns = ["stub_invalid_docstring*"]

        source_files = SourceUtil.get_abs_source_files(
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        if not source_files:
            if verbose:
                print("No source files found.")
            return

        # First count existing fixable violations
        violation_count, _, _ = cls._run_ruff_docstring_check(
            source_files, fix=False, extra_ignore_rules=extra_ignore_rules,
        )

        if violation_count == 0:
            if verbose:
                print("All docstrings comply with pydocstyle formatting rules.")
            return

        # Apply fixes
        cls._run_ruff_docstring_check(source_files, fix=True, extra_ignore_rules=extra_ignore_rules)

        # Verify fixes were applied
        remaining, _, _ = cls._run_ruff_docstring_check(
            source_files, fix=False, extra_ignore_rules=extra_ignore_rules,
        )

        if verbose:
            fixed_count = violation_count - remaining
            print(f"Fixed docstring formatting in {fixed_count} location(s).")
            if remaining > 0:
                print(f"Warning: {remaining} violation(s) could not be auto-fixed.")
