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


def build_package_data(
    package_namespace: str,
    all_packages: tuple[str, ...],
) -> PackageTemplateParams:
    """Build template parameters for a package including isort configuration and package settings.

    Args:
        package_namespace: The package namespace (e.g., 'cl.convince')
        all_packages: All package namespaces from PackageSettings
    """
    # Settings for the specified package
    package_settings = PackageSettings.instance(package=package_namespace)
    package_root = ProjectUtil.get_package_root(package_namespace)

    # Use yaml override for authors if specified, otherwise extract from COPYRIGHT file
    package_authors = package_settings.package_authors or CopyrightUtil.get_authors(package_root, package_namespace)

    # Use yaml override for license if specified, otherwise extract from LICENSE file
    package_license = package_settings.package_license or CopyrightUtil.get_license_name(package_root, package_namespace)

    # Load raw copyright text from the COPYRIGHT file at package root
    copyright_file_path = os.path.join(package_root, "COPYRIGHT")
    with open(copyright_file_path, "r", encoding="utf-8") as f:
        copyright_text = f.read().rstrip("\n")

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

    # Combine dependencies from all included packages in order, do not remove duplicates across packages
    combined_package_dependencies = []
    combined_test_dependencies = []
    for p in included_main_packages:
        pkg_settings = PackageSettings.instance(package=p)
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
        package_init_include=package_settings.package_init_include,
        package_init_exclude=package_settings.package_init_exclude,
        package_copyright=copyright_text,
    )

    return params


def init_packages() -> None:
    """Initialize package files for each package."""

    # Get template directory path relative to where the current Python file is located
    template_dir = Path(__file__).parent / "init_packages"

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

        package_root = Path(ProjectUtil.get_package_root(package))

        # Skip if already processed (shouldn't happen for main packages, but safety check)
        if package_root in processed_roots:
            continue
        processed_roots.add(package_root)

        # Build template params with isort configuration and include/exclude patterns
        params = build_package_data(package, all_packages)

        # Set up include/exclude patterns
        include_patterns = params.package_init_include if params.package_init_include is not None else ["*"]
        exclude_patterns = params.package_init_exclude if params.package_init_exclude is not None else []

        # Use CRLF on Windows, LF on Linux
        newline_char = "\r\n" if platform.system() == "Windows" else "\n"

        # Iterate over each template file, setting file_ext per template
        for template_file in template_dir.rglob("*.j2"):
            # Compute output path by removing .j2 suffix and transforming dot_ prefix
            relative_path = template_file.relative_to(template_dir)
            path_parts = list(relative_path.parts)
            # Substitute {package_path} and {package_namespace} in directory and file names
            path_subs = {
                "{package_path}": params.package_path.split("/"),
                "{package_namespace}": params.package_namespace.split("."),
            }
            output_parts = []
            for i, p in enumerate(path_parts):
                part = transform_part(p.removesuffix(".j2") if i == len(path_parts) - 1 else p)
                if part in path_subs:
                    output_parts.extend(path_subs[part])
                else:
                    output_parts.append(part)
            output_relative_path = Path(*output_parts)

            # Apply include/exclude filters on the output relative path
            output_name = str(output_relative_path)
            if not any(fnmatch.fnmatch(output_name, p) for p in include_patterns):
                continue
            if any(fnmatch.fnmatch(output_name, p) for p in exclude_patterns):
                continue

            # Render template with params converted to dict
            template_text = template_file.read_text(encoding="utf-8")
            content = engine.render(body=template_text, data=params.to_dict())

            # Normalize line endings
            content = content.replace("\r\n", "\n").replace("\r", "\n")

            # Write rendered content with OS-appropriate line endings
            output_file = package_root / output_relative_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8", newline=newline_char) as f:
                f.write(content)


if __name__ == "__main__":
    # Initialize package files
    init_packages()
