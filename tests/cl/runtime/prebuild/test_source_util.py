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
import pytest
from cl.runtime.prebuild.source_util import SourceUtil
from cl.runtime.project.project_layout import ProjectLayout


def _count_py_files_via_os(directory: str, exclude_names: tuple[str, ...]) -> int:
    """Count .py files in a directory tree using a subprocess (cross-platform OS command)."""
    exclude_set = repr(set(exclude_names))
    script = (
        f"import pathlib; "
        f"print(len([p for p in pathlib.Path(r'{directory}').rglob('*.py') "
        f"if p.name not in {exclude_set}]))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"OS command failed: {result.stderr}"
    return int(result.stdout.strip())


def test_source_util():
    """Test SourceUtil.get_source_files with package parameter against an independent OS file count."""

    package = "cl.runtime"
    exclude_names = ("__init__.py",)

    # Get file count from SourceUtil
    source_files = SourceUtil.get_source_files(package=package)
    source_util_count = len(source_files)

    # Get file count independently using OS commands on each package directory
    source_root = ProjectLayout.get_package_source_root(package)
    stubs_root = ProjectLayout.get_package_stubs_root(package)
    tests_root = ProjectLayout.get_package_tests_root(package)

    os_count = 0
    for root_dir in (source_root, stubs_root, tests_root):
        if root_dir is not None:
            os_count += _count_py_files_via_os(root_dir, exclude_names)

    assert source_util_count == os_count, (
        f"SourceUtil found {source_util_count} files but OS command found {os_count} files "
        f"for package '{package}'"
    )
    assert source_util_count > 0, "Expected at least some .py files in the runtime package"


def test_source_util_invalid_package():
    """Test that SourceUtil.get_source_files raises for an unknown package."""

    with pytest.raises(RuntimeError, match="not found in configured packages"):
        SourceUtil.get_source_files(package="cl.nonexistent")


if __name__ == "__main__":
    pytest.main([__file__])
