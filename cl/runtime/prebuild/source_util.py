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
from fnmatch import fnmatch
from typing import Sequence
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.settings.package_settings import PackageSettings


class SourceUtil:
    """Helper class for finding source files across all packages."""

    @classmethod
    def get_source_files(
        cls,
        *,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> list[str]:
        """Get list of source file paths across all packages.

        Args:
            file_include_patterns: Optional list of filename glob patterns to include (default: ['*.py'])
            file_exclude_patterns: Optional list of filename glob patterns to exclude (default: ['__init__.py', '_version.py'])

        Returns:
            List of absolute file paths for all matched source files.
        """

        if file_include_patterns is None:
            file_include_patterns = ["*.py"]
        if file_exclude_patterns is None:
            file_exclude_patterns = ["__init__.py", "_version.py"]

        packages = PackageSettings.instance().get_packages()
        result = []
        all_root_paths = set()

        for package in packages:
            # Add paths to source, stubs, and test directories
            package_root_paths = []
            if (x := ProjectLayout.get_package_source_root(package)) is not None and x not in all_root_paths:
                package_root_paths.append(x)
                all_root_paths.add(x)
            if (x := ProjectLayout.get_package_stubs_root(package)) is not None and x not in all_root_paths:
                package_root_paths.append(x)
                all_root_paths.add(x)
            if (x := ProjectLayout.get_package_tests_root(package)) is not None and x not in all_root_paths:
                package_root_paths.append(x)
                all_root_paths.add(x)

            if not package_root_paths:
                continue

            for root_path in package_root_paths:
                for dir_path, dir_names, filenames in os.walk(root_path):
                    filenames = [x for x in filenames if any(fnmatch(x, y) for y in file_include_patterns)]
                    filenames = [x for x in filenames if not any(fnmatch(x, y) for y in file_exclude_patterns)]
                    for filename in filenames:
                        file_path = os.path.join(dir_path, filename)
                        result.append(str(file_path))

        return result
