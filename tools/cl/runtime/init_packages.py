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
from typing import Sequence

# isort: off
# Ensure bootstrap module can be found and import to configure PYTHONPATH and other settings
# This code block must remain at the top before any other imports
import locate
locate.append_sys_path("../..")
locate.append_sys_path("../../../../runtime")
import cl.runtime.bootstrap
# isort: on

import fnmatch
import os
import platform
from pathlib import Path
from cl.runtime.prebuild.copyright_util import CopyrightUtil
from cl.runtime.prebuild.version_util import VersionUtil
from cl.runtime.project.project_util import ProjectUtil
from cl.runtime.settings.package_settings import PackageSettings
from cl.runtime.templates.jinja_template_engine import JinjaTemplateEngine
from cl.runtime.templates.template_engine import transform_part
from cl.runtime.project.package_template_params import PackageTemplateParams


def get_package_name(package_namespace: str) -> str:
    """Extract the short package name from namespace (e.g., 'cl.convince' -> 'convince')."""
    return package_namespace.split(".")[-1]


def get_isort_section_name(package_namespace: str) -> str:
    """Get isort section name from package namespace (e.g., 'cl.runtime' -> 'CL_RUNTIME')."""
    return package_namespace.replace(".", "_").upper()


def get_isort_known_key(package_namespace: str) -> str:
    """Get isort known_* key from package namespace (e.g., 'cl.runtime' -> 'known_cl_runtime')."""
    return f"known_{package_namespace.replace('.', '_')}"


def build_template_params(
    package_namespace: str,
    pythonpath_packages: Sequence[str],
) -> PackageTemplateParams:
    """Build template parameters for a package including isort configuration and package settings.

    Args:
        package_namespace: The package namespace (e.g., 'cl.runtime') for which params are built
        pythonpath_packages: Package namespaces included in PYTHONPATH
    """
    # Settings for the specified package
    package_settings = PackageSettings.instance(package=package_namespace)
    package_root = ProjectUtil.get_package_root(package_namespace)

    # Use YAML override for authors if specified, otherwise extract from COPYRIGHT file
    package_authors = package_settings.package_authors or CopyrightUtil.get_authors(package_root, package_namespace)

    # Use YAML override for license if specified, otherwise extract from LICENSE file
    package_license = package_settings.package_license or CopyrightUtil.get_license_name(package_root, package_namespace)

    # Load raw copyright text from the COPYRIGHT file at package root
    copyright_file_path = os.path.join(package_root, "COPYRIGHT")
    with open(copyright_file_path, "r", encoding="utf-8") as f:
        copyright_text = f.read().rstrip("\n")

    # Separate main packages from stubs
    main_packages = [p for p in pythonpath_packages if not p.startswith("stubs.")]
    stub_packages = [p for p in pythonpath_packages if p.startswith("stubs.")]

    # Find index of current package in main packages
    package_name = get_package_name(package_namespace)
    try:
        current_index = next(i for i, p in enumerate(main_packages) if get_package_name(p) == package_name)
    except StopIteration:
        # Package not found in main packages (might be a stubs package), use all
        current_index = len(main_packages) - 1

    # Include all main packages up to and including current package
    included_main_packages = main_packages[: current_index + 1]

    # Include stubs for all included main packages
    included_stubs = []
    for mp in included_main_packages:
        mp_name = get_package_name(mp)
        matching_stub = next((s for s in stub_packages if get_package_name(s) == mp_name), None)
        if matching_stub:
            included_stubs.append(matching_stub)

    # Build isort known_* entries for main packages
    isort_known_packages = [
        {
            "known_name": get_isort_known_key(package),
            "known_namespace": package,
            "known_section": get_isort_section_name(package),
        }
        for package in included_main_packages
    ]

    # Build isort known_* entries for stubs, obtaining stubs namespace from package namespace
    isort_known_stubs = [
        {
            "known_name": get_isort_known_key(stub_package := f"stubs.{package}"),
            "known_namespace": stub_package,
            "known_section": get_isort_section_name(stub_package),
        }
        for package in included_main_packages
    ]

    # Build sections list: FUTURE, PYTEST, STDLIB, THIRDPARTY, [main packages], [stubs], FIRSTPARTY, LOCALFOLDER
    sections = ["FUTURE", "PYTEST", "STDLIB", "THIRDPARTY"]
    sections.extend(get_isort_section_name(p) for p in included_main_packages)
    sections.extend(entry["known_section"] for entry in isort_known_stubs)
    sections.extend(["FIRSTPARTY", "LOCALFOLDER"])

    # Combine dependencies from all included packages in order, do not remove duplicates across packages
    combined_package_dependencies = []
    combined_test_dependencies = []
    for package in included_main_packages:
        pkg_settings = PackageSettings.instance(package=package)
        if pkg_settings.package_dependencies:
            combined_package_dependencies.extend(pkg_settings.package_dependencies)
        if pkg_settings.package_test_dependencies:
            combined_test_dependencies.extend(pkg_settings.package_test_dependencies)

    params = PackageTemplateParams(
        package_name=package_settings.package_name,
        package_namespace=package_namespace,
        package_path="/".join(package_namespace.split(".")),
        package_version=VersionUtil.get_package_version(package=package_namespace),
        package_description=package_settings.package_description or "",
        package_requires_python=package_settings.package_requires_python,
        package_license=package_license,
        package_authors=package_authors,
        package_classifiers=package_settings.package_classifiers,
        package_urls=package_settings.package_urls,
        package_dependencies=package_settings.package_dependencies,
        combined_package_dependencies=combined_package_dependencies,
        combined_test_dependencies=combined_test_dependencies,
        package_has_shared_data=package_settings.package_has_shared_data,
        package_has_mypy=package_settings.package_has_mypy,
        main_packages=included_main_packages,
        stub_packages=included_stubs,
        isort_known_packages=isort_known_packages,
        isort_known_stubs=isort_known_stubs,
        isort_sections=sections,
        package_copyright=copyright_text,
    )

    return params


def init_packages() -> None:
    """Initialize package files for each package."""

    # Get template directory path relative to where the current Python file is located
    template_dir = str(Path(__file__).parent / "init_packages")

    # Create Jinja2 template engine
    engine = JinjaTemplateEngine().build()

    # Get all packages from settings
    packages = PackageSettings.instance().get_packages()

    # Track processed package roots to avoid duplicates (stubs share same root as main package)
    processed_roots = set()

    # Iterate over each main package, adding to pythonpath_packages
    pythonpath_packages = []
    for package in packages:

        # Skip stubs packages
        if package.startswith("stubs."):
            continue

        # Build template params object
        pythonpath_packages.append(package)
        params = build_template_params(package, pythonpath_packages)

        # Create Jinja2 template engine and render all templates in the template directory
        engine.render_dir(
            template_dir=template_dir,
            output_dir=ProjectUtil.get_package_root(package),
            data=params,
        )


if __name__ == "__main__":
    # Initialize package files
    init_packages()
