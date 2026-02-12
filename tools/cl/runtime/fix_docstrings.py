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

import sys
from cl.runtime.prebuild.docstring_util import DocstringUtil

if __name__ == '__main__':

    # Parse --ignore D202,D301 style arguments to skip specific rules for this run
    extra_ignore_rules = None
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--ignore" and i + 1 < len(args):
            extra_ignore_rules = [r.strip() for r in args[i + 1].split(",") if r.strip()]

    # Fix docstring formatting issues using ruff pydocstyle rules
    DocstringUtil.fix_docstrings(verbose=True, extra_ignore_rules=extra_ignore_rules)
