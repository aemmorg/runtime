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

from pathlib import Path

from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.project.project_template_params import ProjectTemplateParams
from cl.runtime.project.project_layout_kind import ProjectUtilKind
from cl.runtime.project.project_util import ProjectUtil
from cl.runtime.settings.package_settings import PackageSettings
from cl.runtime.templates.jinja_template_engine import JinjaTemplateEngine


def build_template_params() -> ProjectTemplateParams:
    """Build template parameters for the project including package directories and combined dependencies."""

    # Extract unique package directory names (excluding stubs and ".")
    package_dirs = PackageSettings.instance().get_dirs()

    # Collect combined dependencies from all main packages in order
    all_packages = PackageSettings.instance().get_packages()
    main_packages = [p for p in all_packages if not p.startswith("stubs.")]

    combined_package_dependencies = []
    combined_test_dependencies = []
    for package in main_packages:
        pkg_settings = PackageSettings.instance(package=package)
        if pkg_settings.package_dependencies:
            combined_package_dependencies.extend(pkg_settings.package_dependencies)
        if pkg_settings.package_test_dependencies:
            combined_test_dependencies.extend(pkg_settings.package_test_dependencies)

    result = ProjectTemplateParams(
        packages=package_dirs,
        combined_package_dependencies=combined_package_dependencies,
        combined_test_dependencies=combined_test_dependencies,
    )
    return result


def init_project() -> None:
    """Initialize project files."""

    if (project_layout := ProjectUtil.get_project_layout_kind()) != ProjectUtilKind.MULTIREPO:
        raise RuntimeError(f"Cannot run init_multirepo script when project layout is {project_layout.name.lower()}.")

    # Build template params
    params = build_template_params()

    # Get template directory path relative to where the current Python file is located
    if (layout_kind := ProjectUtil.get_project_layout_kind()) == ProjectUtilKind.MULTIREPO:
        template_dir = str(Path(__file__).parent / "init_project/multirepo")
    elif layout_kind == ProjectUtilKind.MONOREPO:
        template_dir = str(Path(__file__).parent / "init_project/monorepo")
    else:
        raise ErrorUtil.enum_value_error(layout_kind, ProjectUtilKind)

    # Create Jinja2 template engine and render all templates in the template directory
    engine = JinjaTemplateEngine().build()
    engine.render_dir(
        template_dir=template_dir,
        output_dir=ProjectUtil.get_project_root(),
        data=params,
    )


if __name__ == '__main__':

    # Initialize project files
    init_project()
