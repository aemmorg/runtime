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
import ast
import os
import shutil
import tempfile
from cl.runtime.prebuild.inline_imports_util import InlineImportsUtil
from cl.runtime.prebuild.source_util import SourceUtil
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.settings.project_settings import ProjectSettings

_STUBS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../../../stubs/cl/runtime/prebuild"))


def _file_path_to_module(file_path: str, abs_package_dirs: list[str]) -> str:
    """Convert an absolute source file path to a dotted module name relative to a PYTHONPATH entry."""
    file_path_norm = os.path.normpath(file_path)
    for pkg_dir in abs_package_dirs:
        try:
            rel = os.path.relpath(file_path_norm, pkg_dir)
        except ValueError:
            continue
        if rel.startswith("..") or os.path.isabs(rel):
            continue
        return rel.removesuffix(".py").replace(os.sep, ".")
    return os.path.basename(file_path).removesuffix(".py")


def test_no_inline_imports_in_clean_stub():
    """Test that a file without inline imports has no detections."""
    stub_path = os.path.join(_STUBS_DIR, "stub_no_inline_imports.py")
    assert os.path.isfile(stub_path), f"Stub file not found: {stub_path}"
    with open(stub_path, "r", encoding="utf-8") as f:
        source = f.read()
    result = InlineImportsUtil._find_inline_imports(source, stub_path)
    assert len(result) == 0, f"Expected 0 inline imports in stub_no_inline_imports.py, found {len(result)}"


def test_detect_inline_imports_in_stub():
    """Test that inline imports are correctly detected in a file with inline imports."""
    stub_path = os.path.join(_STUBS_DIR, "stub_inline_imports.py")
    assert os.path.isfile(stub_path), f"Stub file not found: {stub_path}"
    with open(stub_path, "r", encoding="utf-8") as f:
        source = f.read()
    result = InlineImportsUtil._find_inline_imports(source, stub_path)
    assert len(result) == 3, f"Expected 3 inline imports in stub_inline_imports.py, found {len(result)}"


def test_inline_imports():
    """Flag inline imports that are not on the permitted list recorded in the expected file.

    Detection uses a heuristic: any import at any nesting level whose line is at or after
    the first non-import, non-docstring top-level statement is reported. To allow a specific
    inline import, add its row to the expected file.
    """
    project_root = ProjectLayout.get_project_root()
    abs_package_dirs = [
        os.path.normpath(os.path.join(project_root, d)) for d in ProjectSettings.instance().get_package_dirs()
    ]
    # Match the most specific directory first so a nested package dir is not shadowed
    abs_package_dirs.sort(key=len, reverse=True)

    source_files = SourceUtil.get_abs_source_files(file_exclude_patterns=["stub_inline_imports*"])

    rows: list[tuple[str, str]] = []
    for file_path in source_files:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        nodes = InlineImportsUtil._find_inline_imports_after_code_begins(source, file_path)
        if not nodes:
            continue

        module = _file_path_to_module(file_path, abs_package_dirs)
        for node in nodes:
            for text in InlineImportsUtil._import_node_to_lines(node):
                rows.append((module, text))

    rows.sort()

    guard = RegressionGuard().build()
    guard.write("Module,Import")
    for module, text in rows:
        guard.write(f"{module},{text}")

    RegressionGuard.verify_all()


def test_fix_inline_imports():
    """Test that inline imports are moved to the top of the file."""
    stub_path = os.path.join(_STUBS_DIR, "stub_inline_imports.py")
    assert os.path.isfile(stub_path), f"Stub file not found: {stub_path}"

    # Verify the stub has inline imports before fixing
    with open(stub_path, "r", encoding="utf-8") as f:
        source = f.read()
    before = InlineImportsUtil._find_inline_imports(source, stub_path)
    assert len(before) > 0, f"Expected inline imports in stub_inline_imports.py, found {len(before)}"

    # Copy to a temp file and apply the fix logic
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        shutil.copy2(stub_path, tmp_path)

        with open(tmp_path, "r", encoding="utf-8") as f:
            source = f.read()

        # Apply the same fix logic used by fix_inline_imports
        inline_imports = InlineImportsUtil._find_inline_imports(source, tmp_path)
        lines = source.split("\n")

        remove_indices = set()
        import_texts = []
        for node, start_line, end_line in inline_imports:
            for line_idx in range(start_line - 1, end_line):
                remove_indices.add(line_idx)
            import_texts.extend(InlineImportsUtil._import_node_to_lines(node))

        new_lines = [line for i, line in enumerate(lines) if i not in remove_indices]
        insert_pos = InlineImportsUtil._find_import_insert_position(new_lines)
        for j, text in enumerate(import_texts):
            new_lines.insert(insert_pos + j, text)

        new_source = "\n".join(new_lines)

        # Verify no inline imports remain after fixing
        after = InlineImportsUtil._find_inline_imports(new_source, tmp_path)
        assert len(after) == 0, f"Expected 0 inline imports after fix, found {len(after)}"

        # Verify the fixed source still parses
        ast.parse(new_source)
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__])
