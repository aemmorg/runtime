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

from dataclasses import dataclass
from cl.runtime.ui.control import Control


@dataclass(slots=True, kw_only=True, eq=False)
class InputControl(Control):
    """Single-line text input control."""

    value: str | None = None
    """Current text value of the input."""

    placeholder: str | None = None
    """Hint text shown when value field is empty."""

    max_chars: int | None = None
    """Maximum allowed characters; None means no limit."""

    width: str | None = "stretch"
    """Width of input area: "stretch" or a pixel value like "200px"."""

    def get_control_type(self) -> str:
        return InputControl.__name__
