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


class MultilineDocstringUtil:
    """Helper class for detecting and fixing multiline docstrings where the opening quotes are on a separate line."""

    @classmethod
    def _run_ruff_d212(
        cls,
        file_paths: list[str],
        *,
        fix: bool = False,
    ) -> tuple[int, str, str]:
        """Run ruff D212 check on the given files, optionally applying fixes.

        Args:
            file_paths: List of absolute file paths to check
            fix: If True, apply fixes in place

        Returns:
            Tuple of (total_violation_count, combined_stdout, combined_stderr).
        """

        total_violations = 0
        all_stdout = []
        all_stderr = []

        for i in range(0, len(file_paths), _MAX_CMD_BATCH):
            batch = file_paths[i : i + _MAX_CMD_BATCH]
            cmd = [sys.executable, "-m", "ruff", "check", "--select", "D212"]
            if fix:
                cmd.append("--fix")
            cmd.extend(batch)
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.stdout:
                all_stdout.append(result.stdout)
            if result.stderr:
                all_stderr.append(result.stderr)
            # Count violations from output lines matching the D212 pattern
            for line in result.stdout.splitlines():
                if ": D212 " in line:
                    total_violations += 1

        return total_violations, "\n".join(all_stdout), "\n".join(all_stderr)

    @classmethod
    def test_multiline_docstrings(
        cls,
        *,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> None:
        """Test that no multiline docstrings have the opening quotes on a separate line.

        Raises RuntimeError with a list of violations if any are found.

        Args:
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        if file_exclude_patterns is None:
            file_exclude_patterns = ["_version.py"]

        source_files = SourceUtil.get_source_files(
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        if not source_files:
            return

        violation_count, stdout, stderr = cls._run_ruff_d212(source_files, fix=False)

        if violation_count > 0:
            raise RuntimeError(
                f"Multi-line docstring summary should start at the first line (D212) "
                f"in {violation_count} location(s):\n{stdout}"
            )

    @classmethod
    def fix_multiline_docstrings(
        cls,
        *,
        verbose: bool = False,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> None:
        """Fix multiline docstrings where the opening quotes are on a separate line.

        Args:
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        if file_exclude_patterns is None:
            file_exclude_patterns = ["_version.py"]

        source_files = SourceUtil.get_source_files(
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        if not source_files:
            if verbose:
                print("No source files found.")
            return

        # First count existing violations
        violation_count, _, _ = cls._run_ruff_d212(source_files, fix=False)

        if violation_count == 0:
            if verbose:
                print("All multiline docstrings already have summary on the first line.")
            return

        # Apply fixes
        cls._run_ruff_d212(source_files, fix=True)

        # Verify fixes were applied
        remaining, _, _ = cls._run_ruff_d212(source_files, fix=False)

        if verbose:
            fixed_count = violation_count - remaining
            print(f"Fixed multiline docstring opening quotes in {fixed_count} location(s).")
            if remaining > 0:
                print(f"Warning: {remaining} violation(s) could not be auto-fixed.")
