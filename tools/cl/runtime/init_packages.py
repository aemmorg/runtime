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
locate.append_sys_path("../..")
locate.append_sys_path("../../../../runtime")
import cl.runtime.bootstrap
# isort: on

from pathlib import Path
from cl.runtime.prebuild.copyright_util import CopyrightUtil
from cl.runtime.prebuild.version_util import VersionUtil
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.settings.package_settings import PackageSettings
from cl.runtime.templates.jinja_template_engine import JinjaTemplateEngine


def get_package_name(package_namespace: str) -> str:
    """Extract the short package name from namespace (e.g., 'cl.convince' -> 'convince')."""
    return package_namespace.split(".")[-1]


def get_isort_section_name(package_namespace: str) -> str:
    """Get isort section name from package namespace (e.g., 'cl.runtime' -> 'CL_RUNTIME')."""
    return package_namespace.replace(".", "_").upper()


def get_isort_known_key(package_namespace: str) -> str:
    """Get isort known_* key from package namespace (e.g., 'cl.runtime' -> 'known_cl_runtime')."""
    return f"known_{package_namespace.replace('.', '_')}"


def build_package_data(package_namespace: str, all_packages: tuple[str, ...]) -> dict:
    """
    Build template data for a package including isort configuration and package settings.

    Args:
        package_namespace: The package namespace (e.g., 'cl.convince')
        all_packages: All package namespaces from PackageSettings

    Returns:
        Dict with template data including isort config and package settings
    """
    # Settings for the specified package
    package_settings = PackageSettings.instance(package=package_namespace)
    package_root = ProjectLayout.get_package_root(package_namespace)

    # Use yaml override for authors if specified, otherwise extract from COPYRIGHT file
    package_authors = package_settings.package_authors or CopyrightUtil.get_authors(package_root, package_namespace)

    # Use yaml override for license if specified, otherwise extract from LICENSE file
    package_license = package_settings.package_license or CopyrightUtil.get_license_name(package_root, package_namespace)

    # Separate main packages from stubs
    main_packages = [p for p in all_packages if not p.startswith("stubs.")]
    stub_packages = [p for p in all_packages if p.startswith("stubs.")]

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
    isort_known_packages = []
    for p in included_main_packages:
        isort_known_packages.append(
            {
                "key": get_isort_known_key(p),
                "value": p,
                "section": get_isort_section_name(p),
            }
        )

    # Build isort known_* entries for stubs
    isort_known_stubs = []
    for s in included_stubs:
        isort_known_stubs.append(
            {
                "key": get_isort_known_key(s),
                "value": s,
                "section": get_isort_section_name(s),
            }
        )

    # Build sections list: FUTURE, PYTEST, STDLIB, THIRDPARTY, [main packages], [stubs], FIRSTPARTY, LOCALFOLDER
    sections = ["FUTURE", "PYTEST", "STDLIB", "THIRDPARTY"]
    sections.extend(get_isort_section_name(p) for p in included_main_packages)
    sections.extend(entry["section"] for entry in isort_known_stubs)
    sections.extend(["FIRSTPARTY", "LOCALFOLDER"])

    return {
        "package_name": package_settings.package_name,  # Readable name, e.g., "Runtime"
        "package_namespace": package_namespace,  # Dot-delimited package namespace, e.g., 'cl.runtime'
        "package_path": "/".join(package_namespace.split(".")),  # Slash-delimited package namespace, e.g., 'cl/runtime'
        "package_version": VersionUtil.get_package_version(package=package_namespace),
        "package_description": package_settings.package_description or "",
        "package_requires_python": package_settings.package_requires_python,
        "package_license": package_license,
        "package_authors": package_authors,
        "package_classifiers": list(package_settings.package_classifiers) if package_settings.package_classifiers else [],
        "package_urls": package_settings.package_urls,
        "package_dependencies": list(package_settings.package_dependencies) if package_settings.package_dependencies else [],
        "package_has_shared_data": package_settings.package_has_shared_data,
        "package_has_mypy": package_settings.package_has_mypy,
        "main_packages": included_main_packages,
        "stub_packages": included_stubs,
        "isort_known_packages": isort_known_packages,
        "isort_known_stubs": isort_known_stubs,
        "isort_sections": sections,
    }


def init_packages() -> None:
    """Initialize package files for each package."""

    # Get template directory path relative to where the current Python file is located
    template_dir = str(Path(__file__).parent / "init_packages")

    # Create Jinja2 template engine
    engine = JinjaTemplateEngine().build()

    # Get all packages from settings
    all_packages = PackageSettings.instance().get_packages()

    # Track processed package roots to avoid duplicates (stubs share same root as main package)
    processed_roots = set()

    # Iterate over each main package (skip stubs as they share the same package root)
    for package in all_packages:
        # Skip stubs packages - they share the package root with main package
        if package.startswith("stubs."):
            continue

        package_root = ProjectLayout.get_package_root(package)

        # Skip if already processed (shouldn't happen for main packages, but safety check)
        if package_root in processed_roots:
            continue
        processed_roots.add(package_root)

        # Build template data with isort configuration
        data = build_package_data(package, all_packages)

        engine.render_dir(input_dir=template_dir, output_dir=package_root, data=data)


if __name__ == "__main__":
    # Initialize package files
    init_packages()
