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

import argparse

from cl.runtime.prebuild.version_util import VersionUtil
from cl.runtime.project.package_util import PackageUtil

if __name__ == "__main__":

    # Update version for the specified module or modules
    parser = argparse.ArgumentParser(description="Bump the version of a package or module.")
    parser.add_argument(
        "--module",
        type=str,
        required=True,
        action="append",
        help="Dot-delimited module namespace to bump.",
    )
    args = parser.parse_args()

    print("Updated version(s):")
    for module in args.module:
        version = VersionUtil.bump_module_version(module=module)
        print(f"{module}: {version}")

