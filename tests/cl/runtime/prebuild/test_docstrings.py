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

import pytest
import os
import subprocess
import sys
from cl.runtime.prebuild.docstring_util import DocstringUtil

_STUBS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "stubs", "cl", "runtime", "prebuild")
)

_RUFF_D_ARGS = [
    sys.executable,
    "-m",
    "ruff",
    "check",
    "--output-format",
    "concise",
    "--select",
    "D",
    "--ignore",
    "D100,D101,D102,D103,D104,D105,D106,D107,D200,D202,D203,D205,D212,D213,"
    "D301,D400,D401,D402,D403,D404,D410,D411,D413,D415,D417",
]
"""Base ruff command for enforced pydocstyle checks (select D, ignore failing rules)."""


def _count_ruff_d_violations(file_path: str) -> int:
    """Run ruff pydocstyle checks on a single file and return the number of violations."""
    result = subprocess.run(
        _RUFF_D_ARGS + [file_path],
        capture_output=True,
        text=True,
    )
    count = 0
    for line in result.stdout.splitlines():
        if ": D" in line and " [" in line:
            count += 1
    return count


def test_correct_docstrings():
    """Test that the stub file with correct docstrings has no pydocstyle violations."""
    stub_path = os.path.join(_STUBS_DIR, "stub_correct_docstrings.py")
    assert os.path.isfile(stub_path), f"Stub file not found: {stub_path}"
    violation_count = _count_ruff_d_violations(stub_path)
    assert (
        violation_count == 0
    ), f"Expected 0 pydocstyle violations in stub_correct_docstrings.py, found {violation_count}"


def test_docstrings():
    """Prebuild test to check that docstrings comply with pydocstyle formatting rules."""
    # Test that all source files have correct docstring format
    DocstringUtil.validate_docstrings()


if __name__ == "__main__":
    pytest.main([__file__])
