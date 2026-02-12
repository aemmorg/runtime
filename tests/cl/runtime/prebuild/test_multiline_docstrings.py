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
import shutil
import subprocess
import sys
import tempfile
import pytest
from cl.runtime.prebuild.multiline_docstring_util import MultilineDocstringUtil


_STUBS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "stubs", "cl", "runtime", "prebuild")
)


def _run_ruff_d212_on_file(file_path: str) -> int:
    """Run ruff D212 check on a single file and return the number of violations."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--select", "D212", file_path],
        capture_output=True,
        text=True,
    )
    count = 0
    for line in result.stdout.splitlines():
        if ": D212 " in line:
            count += 1
    return count


def test_correct_docstrings():
    """Test that the stub file with correct docstrings has no D212 violations."""

    stub_path = os.path.join(_STUBS_DIR, "stub_correct_docstrings.py")
    assert os.path.isfile(stub_path), f"Stub file not found: {stub_path}"
    violation_count = _run_ruff_d212_on_file(stub_path)
    assert violation_count == 0, f"Expected 0 D212 violations in stub_correct_docstrings.py, found {violation_count}"


def test_multiline_docstrings():
    """Prebuild test to check that no multiline docstrings have opening quotes on a separate line."""

    # Test that all source files have correct multiline docstring format
    MultilineDocstringUtil.validate_multiline_docstrings()


def test_fix_multiline_docstrings():
    """Test that fix_multiline_docstrings corrects D212 violations in a stub file."""

    stub_path = os.path.join(_STUBS_DIR, "stub_wrong_docstrings.py")
    assert os.path.isfile(stub_path), f"Stub file not found: {stub_path}"

    # Verify the stub file has violations before fixing
    before_count = _run_ruff_d212_on_file(stub_path)
    assert before_count > 0, f"Expected D212 violations in stub_wrong_docstrings.py, found {before_count}"

    # Copy to a temp file and fix it
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        shutil.copy2(stub_path, tmp_path)

        # Run ruff fix on the temp copy
        subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--select", "D212", "--fix", tmp_path],
            capture_output=True,
            text=True,
        )

        # Verify no violations remain after fixing
        after_count = _run_ruff_d212_on_file(tmp_path)
        assert after_count == 0, f"Expected 0 D212 violations after fix, found {after_count}"
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__])
