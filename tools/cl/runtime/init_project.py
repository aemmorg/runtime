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

# isort: off
# Ensure bootstrap module can be found and import to configure PYTHONPATH and other settings
# This code block must remain at the top before any other imports
import locate
locate.append_sys_path("../../..")
import cl.runtime.bootstrap
# isort: on

import argparse
import subprocess
import sys
from pathlib import Path
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.project.project_template_params import ProjectTemplateParams
from cl.runtime.project.project_layout_kind import ProjectLayoutKind
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.settings.package_settings import PackageSettings
from cl.runtime.settings.project_settings import ProjectSettings
from cl.runtime.templates.jinja_template_engine import JinjaTemplateEngine


def build_template_params() -> ProjectTemplateParams:
    """Build template parameters for the project including package directories and path dependencies."""

    # Extract unique package directory names (excluding stubs and ".")
    package_dirs = ProjectSettings.instance().get_package_dirs()

    # Collect main packages and build path-dependency entries
    all_packages = ProjectSettings.instance().get_packages()
    project_dirs_map = ProjectSettings.instance().project_dirs
    main_packages = [p for p in all_packages if not p.startswith("stubs.")]

    main_package_entries = []
    combined_test_dependencies = []
    for package in main_packages:
        pkg_settings = PackageSettings.instance(package=package)

        # Build path-dependency entry with package name and relative directory
        pkg_dir = project_dirs_map[package]
        entry = {
            "name": pkg_settings.package_name or package.split(".")[-1],
            "path": pkg_dir,
        }
        main_package_entries.append(entry)

        # Collect test deps (concatenated without dep-tree resolution)
        if pkg_settings.package_test_dependencies:
            combined_test_dependencies.extend(pkg_settings.package_test_dependencies)

    result = ProjectTemplateParams(
        package_dirs=package_dirs,
        main_package_entries=main_package_entries,
        combined_test_dependencies=combined_test_dependencies if combined_test_dependencies else None,
    )
    return result


def init_project(force: bool = False) -> None:
    """
    Initialize project files.
    Args:
        force: If True, overwrite project files even if they already exist
    """

    if (project_layout := ProjectLayout.get_project_layout_kind()) != ProjectLayoutKind.MULTIREPO:
        raise RuntimeError(f"Cannot run init_multirepo script when project layout is {project_layout.name.lower()}.")

    # Build template params
    params = build_template_params()

    # Get template directory path relative to where the current Python file is located
    if (layout_kind := ProjectLayout.get_project_layout_kind()) == ProjectLayoutKind.MULTIREPO:
        template_dir = str(Path(__file__).parent / "init_project/multirepo")
    elif layout_kind == ProjectLayoutKind.MONOREPO:
        template_dir = str(Path(__file__).parent / "init_project/monorepo")
    else:
        raise ErrorUtil.enum_value_error(layout_kind, ProjectLayoutKind)

    # Create Jinja2 template engine and render all templates in the template directory
    engine = JinjaTemplateEngine().build()
    engine.render_dir(
        template_dir=template_dir,
        output_dir=ProjectLayout.get_project_root(),
        data=params,
        force=force,
    )

    # Run update_requirements to resolve the full dependency tree (uv/poetry/pip-compile)
    # and generate the unified requirements.txt at project root
    update_requirements_script = str(Path(__file__).parent / "update_requirements.py")
    project_root = ProjectUtil.get_project_root()
    subprocess.run(
        [sys.executable, update_requirements_script, "--project-root", project_root],
        check=True,
    )


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Initialize packages with setup files and scripts")
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force create package files without checking if they already exist."
    )
    args = parser.parse_args()

    # Initialize project files
    init_project(force=args.force)
