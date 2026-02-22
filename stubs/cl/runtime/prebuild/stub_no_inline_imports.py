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

import json
import os
from collections import OrderedDict
from pathlib import Path


def function_without_inline_import():
    """Function that has no inline imports."""
    return json.dumps({"cwd": os.getcwd()})


def another_function():
    """Another function without inline imports."""
    return str(Path.cwd())


class ClassWithoutInlineImport:
    """Class with methods that have no inline imports."""

    def method_without_import(self):
        """Method without inline import."""
        return OrderedDict()
