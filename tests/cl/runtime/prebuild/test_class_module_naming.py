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

import ast
import os
import pytest
from cl.runtime.prebuild.source_util import SourceUtil
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.project.project_layout import ProjectLayout


def _find_class_module_mismatches(
    source_files: tuple[str, ...],
    project_root: str,
) -> list[tuple[str, str, str]]:
    """Find class/module naming mismatches in the given source files.

    Returns:
        List of (rel_path, class_name, module_name) tuples for each mismatch.
    """

    mismatches: list[tuple[str, str, str]] = []
    for file_path in source_files:
        module_name = os.path.splitext(os.path.basename(file_path))[0]

        # Parse the file to find class definitions
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=file_path)
            except SyntaxError:
                continue

        # Find top-level class definitions
        class_names = [node.name for node in ast.iter_child_nodes(tree) if isinstance(node, ast.ClassDef)]

        # For each class, check if its lowercase name matches the module name with underscores removed
        module_name_lower_no_underscores = module_name.replace("_", "").lower()
        for class_name in class_names:
            class_name_lower = class_name.lower()
            if class_name_lower != module_name_lower_no_underscores:
                continue

            # Lowercase match found, verify case correctness in both directions
            rel_path = os.path.relpath(file_path, project_root)
            try:
                expected_snake = CaseUtil.pascal_to_snake_case(class_name)
            except RuntimeError:
                mismatches.append((rel_path, class_name, module_name))
                continue

            try:
                expected_pascal = CaseUtil.snake_to_pascal_case(module_name)
            except RuntimeError:
                mismatches.append((rel_path, class_name, module_name))
                continue

            if expected_snake != module_name or expected_pascal != class_name:
                mismatches.append((rel_path, class_name, module_name))

    return mismatches


def test_class_module_naming():
    """Test that class names and module names follow consistent PascalCase/snake_case conventions."""

    project_root = ProjectLayout.get_project_root()
    source_files = SourceUtil.get_abs_source_files(file_exclude_patterns=["__init__.py", "stub_case_mismatch*"])

    mismatches = _find_class_module_mismatches(source_files, project_root)
    if mismatches:
        total = len(mismatches)
        parts = [f"Found {total} class/module naming mismatch(es):\n"]
        for rel_path, class_name, module_name in mismatches:
            parts.append(f"  {rel_path}")
            parts.append(f"    Class '{class_name}' does not match module '{module_name}'")
        error_msg = "\n".join(parts)
        raise RuntimeError(error_msg)


def test_detect_case_mismatch_in_stub():
    """Test that a class with incorrect PascalCase casing is detected as a mismatch."""

    stubs_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../../../stubs/cl/runtime/prebuild"))
    stub_path = os.path.join(stubs_dir, "stub_case_mismatch.py")
    assert os.path.isfile(stub_path), f"Stub file not found: {stub_path}"

    project_root = ProjectLayout.get_project_root()
    mismatches = _find_class_module_mismatches((stub_path,), project_root)
    assert len(mismatches) == 1, f"Expected 1 mismatch in stub_case_mismatch.py, found {len(mismatches)}"
    assert mismatches[0][1] == "StubCaseMisMatch"
    assert mismatches[0][2] == "stub_case_mismatch"


if __name__ == "__main__":
    pytest.main([__file__])
