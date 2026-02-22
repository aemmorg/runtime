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


def function_with_inline_import():
    """Function that has an inline import."""
    import json
    return json.dumps({"cwd": os.getcwd()})


def function_with_from_import():
    """Function that has an inline from-import."""
    from pathlib import Path
    return str(Path.cwd())


class ClassWithInlineImport:
    """Class with a method that has an inline import."""

    def method_with_import(self):
        """Method with inline import."""
        from collections import OrderedDict
        return OrderedDict()
