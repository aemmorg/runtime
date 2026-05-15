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
from cl.runtime.settings.project_settings import ProjectSettings


class SourceUtil:
    """Helper class for finding source files across all packages."""

    @classmethod
    def get_abs_source_files(
        cls,
        *,
        package: str | None = None,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
        skip_empty_files: bool = True,
    ) -> tuple[str, ...]:
        """Get list of source file paths across all packages or a single package.

        Args:
            package: Optional dot-delimited package name to filter by (e.g., 'cl.runtime')
            file_include_patterns: Optional list of filename glob patterns to include (default: ['*.py'])
            file_exclude_patterns: Optional list of filename glob patterns to exclude (default: ['__init__.py'])
            skip_empty_files: If True, exclude files that are empty (0 bytes) from the results (default: True)

        Returns:
            List of absolute file paths for all matched source files.
        """

        if file_include_patterns is None:
            file_include_patterns = ["*.py"]

        # Exclude __init__.py files only when processing empty files is requested.
        # Otherwise, non-empty __init__.py files should be processed as well as other source files.
        if file_exclude_patterns is None:
            file_exclude_patterns = [] if skip_empty_files else ["__init__.py"]

        all_packages = ProjectSettings.instance().get_packages()
        if package is not None:
            if package in all_packages:
                packages = (package,)
            else:
                all_packages_str = "\n".join(all_packages)
                raise RuntimeError(f"Package '{package}' not found in configured packages:\n{all_packages_str}")
        else:
            packages = all_packages

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
                        if skip_empty_files and os.path.getsize(file_path) == 0:
                            continue
                        result.append(str(file_path))

        return tuple(result)
