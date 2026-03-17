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


def test_module_and_class_naming():
    """Prebuild test to check that module names and class names follow CaseUtil conversion rules."""

    project_root = ProjectLayout.get_project_root()
    source_files = SourceUtil.get_abs_source_files()

    errors = []
    for abs_path in source_files:
        # Get module name without .py extension
        module_name = os.path.splitext(os.path.basename(abs_path))[0]

        # Skip modules that start with test_ or stub_ as they follow different naming conventions
        if module_name.startswith("test_") or module_name.startswith("stub_"):
            continue

        # Normalized module name for comparison (lowercase, no underscores)
        module_normalized = module_name.lower().replace("_", "")

        # Parse the file to find class definitions
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=abs_path)
        except SyntaxError:
            continue

        # Get top-level class definitions
        class_names = [node.name for node in ast.iter_child_nodes(tree) if isinstance(node, ast.ClassDef)]

        # Get path relative to project root for error messages
        rel_path = os.path.relpath(abs_path, project_root)

        for class_name in class_names:
            # Normalized class name for comparison (lowercase, no underscores)
            class_normalized = class_name.lower().replace("_", "")

            # Check only classes whose name matches the module name when normalized
            if module_normalized != class_normalized:
                continue

            # Check that module name is valid snake_case
            if not CaseUtil.is_snake_case(module_name):
                errors.append(
                    f"Module '{rel_path}': module name '{module_name}' is not valid snake_case"
                )
                continue

            # Check that class name is valid PascalCase
            if not CaseUtil.is_pascal_case(class_name):
                errors.append(
                    f"Module '{rel_path}': class name '{class_name}' is not valid PascalCase"
                )
                continue

            # Check snake_to_pascal_case: module name should convert to the actual class name
            expected_class_name = CaseUtil.snake_to_pascal_case(module_name)

            if expected_class_name != class_name:
                errors.append(
                    f"Module '{rel_path}': CaseUtil.snake_to_pascal_case('{module_name}') "
                    f"= '{expected_class_name}', actual class name '{class_name}'"
                )
                continue

            # Check pascal_to_snake_case: class name should convert back to the module name
            expected_module_name = CaseUtil.pascal_to_snake_case(class_name)

            if expected_module_name != module_name:
                errors.append(
                    f"Module '{rel_path}': CaseUtil.pascal_to_snake_case('{class_name}') "
                    f"= '{expected_module_name}', actual module name '{module_name}'"
                )

    if errors:
        errors_str = "\n".join(errors)
        raise RuntimeError(
            f"Found {len(errors)} module/class naming inconsistencies:\n{errors_str}"
        )


if __name__ == "__main__":
    pytest.main([__file__])
