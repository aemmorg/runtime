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
from cl.runtime.ui.control.input_control import InputControl


@dataclass(slots=True, kw_only=True, eq=False)
class TextAreaControl(InputControl):
    """Multi-line text input control."""

    height: str | None = "stretch"
    """Height of the editor area: "stretch" or a pixel value (e.g. "200px")."""

    wrap_lines: bool = True
    """Whether to wrap lines inside the editor (True) or allow horizontal scroll (False)."""

    def get_control_type(self) -> str:
        return TextAreaControl.__name__
