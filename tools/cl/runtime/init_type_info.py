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

import os
import sys
from cl.runtime.prebuild.init_file_util import InitFileUtil
from cl.runtime.prebuild.module_info import ModuleInfo
from cl.runtime.prebuild.source_util import SourceUtil
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.settings.package_settings import PackageSettings


def init_type_info() -> None:
    """Create __init__.py files to avoid missing directories and rebuild type cache."""

    settings_env = os.environ.get("CL_SETTINGS_ENV", "development")
    print(f"Environment: {settings_env}")

    # Parse --force flag
    force = "--force" in sys.argv[1:]

    # Create __init__.py files first to avoid missing classes in directories without __init__.py
    print("Adding __init__.py files if any are missing...")
    InitFileUtil.check_or_fix_init_files(fix=True, verbose=False)

    # Compute current file hashes
    print("Computing source file hashes...")
    source_files = SourceUtil.get_source_files()
    current_hashes = ModuleInfo.compute_hashes(source_files)

    # Also hash settings.yaml since it controls which packages are scanned
    settings_yaml_path = os.path.join(ProjectLayout.get_project_root(), "settings.yaml")
    if os.path.exists(settings_yaml_path):
        current_hashes["settings.yaml"] = ModuleInfo.compute_file_hash(settings_yaml_path)

    # Check if TypeInfo.csv exists
    type_info_path = os.path.join(ProjectLayout.get_resources_root(), "bootstrap/TypeInfo.csv")
    type_info_exists = os.path.exists(type_info_path)

    # Fast path: no changes detected and TypeInfo.csv exists
    if not force and not ModuleInfo.has_changes(current_hashes) and type_info_exists:
        print("No source file changes detected, skipping type cache rebuild.")
        return

    # Full rebuild
    if force:
        print("Force flag set, rebuilding type cache...")
    else:
        print("Source file changes detected, rebuilding type cache...")
    packages = PackageSettings.instance().get_packages()
    TypeInfo.rebuild(packages=packages)

    # Save updated hashes only after successful rebuild
    ModuleInfo.save(current_hashes)
    print("Type cache rebuild complete.")

    print(f"TypeInfo.csv written to: {TypeInfo._get_preload_filename()}")


if __name__ == '__main__':

    # Initialize type cache
    init_type_info()
