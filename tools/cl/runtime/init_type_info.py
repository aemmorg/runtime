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

from cl.runtime.project.resources_util import ResourcesUtil

locate.append_sys_path("../../..")
import cl.runtime.bootstrap
# isort: on

import sys
from cl.runtime.settings.dynaconf_loader import DynaconfLoader
from cl.runtime.schema.type_info import TypeInfo


def init_type_info() -> None:
    """Create __init__.py files to avoid missing directories and rebuild type cache."""

    settings_env = DynaconfLoader.instance().get_settings_env()
    print(f"Rebuilding TypeInfo.csv for Dynaconf environment: {settings_env}")

    # Always update if invoked directly rather than from another script or a test
    TypeInfo.rebuild(force=True)

if __name__ == '__main__':

    # Initialize type cache
    init_type_info()
