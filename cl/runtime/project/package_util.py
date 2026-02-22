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
from cl.runtime.settings.package_settings import PackageSettings


class PackageUtil:
    """Utility class for determining the current package from a file path."""

    @classmethod
    def get_current_package(cls, caller_file: str) -> str:
        """Get the main package namespace whose root contains the specified file.

        Args:
            caller_file: The __file__ of the calling module, used to determine the package.

        Returns:
            Dot-delimited package namespace, e.g., 'cl.runtime'
        """

        caller_dir = os.path.normpath(os.path.abspath(os.path.dirname(caller_file)))
        project_root = os.path.normpath(ProjectUtil.get_project_root())
        package_dirs = PackageSettings.instance().package_dirs

        for namespace, directory in package_dirs.items():
            # Skip stubs packages
            if namespace.startswith("stubs."):
                continue
            package_root = os.path.normpath(os.path.join(project_root, directory))
            # Match the package root itself or any subdirectory
            if caller_dir == package_root or caller_dir.startswith(package_root + os.sep):
                return namespace

        raise RuntimeError(
            f"File '{caller_file}' is not under any main package root.\n"
            f"Known package directories: {dict(package_dirs)}"
        )
