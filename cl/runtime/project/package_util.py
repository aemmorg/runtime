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

import os
from cl.runtime.project.project_util import ProjectUtil
from cl.runtime.settings.project_settings import ProjectSettings


class PackageUtil:
    """Utility class for determining the current package from a file path."""

    @classmethod
    def get_containing_package(cls, module: str) -> str:
        """Get the package namespace that contains the specified module.

        Args:
            module: Dot-delimited module namespace, e.g., 'cl.runtime.prebuild'

        Returns:
            Dot-delimited package namespace, e.g., 'cl.runtime'
        """

        # Sort by namespace length descending to find the most specific match
        project_dirs = ProjectSettings.instance().project_dirs
        for namespace in sorted(project_dirs, key=len, reverse=True):
            if module == namespace or module.startswith(namespace + "."):
                return namespace

        raise RuntimeError(
            f"Module '{module}' is not under any known package namespace.\n"
            f"Known package namespaces: {list(project_dirs)}"
        )

    @classmethod
    def get_file_package(cls, caller_file: str) -> str:
        """Get the main package namespace whose root contains the specified file.

        Args:
            caller_file: The __file__ of the calling module, used to determine the package.

        Returns:
            Dot-delimited package namespace, e.g., 'cl.runtime'
        """

        caller_dir = os.path.normpath(os.path.abspath(os.path.dirname(caller_file)))
        project_root = os.path.normpath(ProjectUtil.get_project_root())
        project_dirs = ProjectSettings.instance().project_dirs

        for namespace, directory in project_dirs.items():
            # Skip stubs packages
            if namespace.startswith("stubs."):
                continue
            package_root = os.path.normpath(os.path.join(project_root, directory))
            # Match the package root itself or any subdirectory
            if caller_dir == package_root or caller_dir.startswith(package_root + os.sep):
                return namespace

        raise RuntimeError(
            f"File '{caller_file}' is not under any main package root.\n"
            f"Known package directories: {dict(project_dirs)}"
        )
