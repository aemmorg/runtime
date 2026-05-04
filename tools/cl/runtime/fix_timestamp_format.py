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

from cl.runtime.prebuild.timestamp_format_util import TimestampFormatUtil
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.settings.project_settings import ProjectSettings

if __name__ == '__main__':

    # The list of packages from context settings
    packages = ProjectSettings.instance().get_packages()

    dirs = set()
    for package in packages:
        # Add paths to source, stubs, tests, and preloads directories
        if (x := ProjectLayout.get_package_source_root(package)) is not None and x not in dirs:
            dirs.add(x)
        if (x := ProjectLayout.get_package_stubs_root(package)) is not None and x not in dirs:
            dirs.add(x)
        if (x := ProjectLayout.get_package_tests_root(package)) is not None and x not in dirs:
            dirs.add(x)
        if (x := ProjectLayout.get_package_preloads_root(package)) is not None and x not in dirs:
            dirs.add(x)

    # Check and fix all legacy timestamp formats
    TimestampFormatUtil.check_or_fix_format(
        dirs=tuple(dirs),
        fix=True,
        verbose=True,
        # Prevent fixing of test files that use intentionally invalid (legacy) timestamp formats
        file_exclude_patterns=[
            "invalid_timestamp_*",
            "test_timestamp_format.py",
            "test_timestamp.py",
        ],
        dir_exclude_patterns=[
            "test_timestamp",
            "test_timestamp_format",
        ],
    )
