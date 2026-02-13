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
import sys

# Pre-parse --env from sys.argv before bootstrap so Dynaconf picks up the environment
_env_value = None
for i, arg in enumerate(sys.argv):
    if arg == "--env" and i + 1 < len(sys.argv):
        _env_value = sys.argv[i + 1]
        break
    if arg.startswith("--env="):
        _env_value = arg.split("=", 1)[1]
        break
if _env_value is not None:
    os.environ["CL_SETTINGS_ENV"] = _env_value

import locate

# Add runtime/ to sys.path so both cl.* and tools.* packages are importable
locate.append_sys_path("../../..")

import cl.runtime.bootstrap  # isort: skip

from cl.runtime.cli.main import cli

if __name__ == "__main__":
    cli()
