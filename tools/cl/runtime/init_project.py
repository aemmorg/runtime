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
from cl.runtime.project.project_layout_kind import ProjectLayoutKind
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.settings.package_settings import PackageSettings
from cl.runtime.templates.jinja_template_engine import JinjaTemplateEngine


def collect_all_requirements(all_packages: tuple[str, ...]) -> dict:
    """Collect and combine requirements from all main packages in package_dirs order."""

    # Only process main packages (not stubs)
    main_packages = [p for p in all_packages if not p.startswith("stubs.")]

    # Combine requirements from all packages in order, do not remove duplicates
    combined_package_requirements = []
    combined_build_requirements = []
    combined_test_requirements = []

    for package in main_packages:
        pkg_settings = PackageSettings.instance(package=package)
        if pkg_settings.package_requirements:
            combined_package_requirements.extend(pkg_settings.package_requirements)
        if pkg_settings.package_build_requirements:
            combined_build_requirements.extend(pkg_settings.package_build_requirements)
        if pkg_settings.package_test_requirements:
            combined_test_requirements.extend(pkg_settings.package_test_requirements)

    return {
        "package_requirements": combined_package_requirements,
        "build_requirements": combined_build_requirements,
        "test_requirements": combined_test_requirements,
    }


def init_project() -> None:
    """Initialize project files."""

    if (project_layout := ProjectLayout.get_project_layout_kind()) != ProjectLayoutKind.MULTIREPO:
        raise RuntimeError(f"Cannot run init_multirepo script when project layout is {project_layout.name.lower()}.")

    # Extract unique package directory names (excluding stubs and ".")
    # Filter to only get main packages (cl.*) and their directory values
    package_dirs = PackageSettings.instance().get_dirs()

    # Collect combined requirements from all packages in package_dirs order
    all_packages = PackageSettings.instance().get_packages()
    requirements = collect_all_requirements(all_packages)

    # Get project root
    project_root = Path(ProjectLayout.get_project_root())

    # Get template directory path relative to where the current Python file is located
    if (layout_kind := ProjectLayout.get_project_layout_kind()) == ProjectLayoutKind.MULTIREPO:
        template_dir = str(Path(__file__).parent / "init_project/multirepo")
    elif layout_kind == ProjectLayoutKind.MONOREPO:
        template_dir = str(Path(__file__).parent / "init_project/monorepo")
    else:
        raise ErrorUtil.enum_value_error(layout_kind, ProjectLayoutKind)

    # Create Jinja2 template engine and render all templates
    engine = JinjaTemplateEngine().build()
    data = {"packages": package_dirs, **requirements}
    engine.render_dir(input_dir=template_dir, output_dir=project_root, data=data)


if __name__ == '__main__':

    # Initialize project files
    init_project()
