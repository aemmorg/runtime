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
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.ui.control import Control


@dataclass(slots=True, kw_only=True, eq=False)
class SliderControl(Control):
    """Numeric slider control for selecting a value within a range."""

    min_value: float = required()
    """Minimum allowed value for the slider."""

    max_value: float = required()
    """Maximum allowed value for the slider."""

    selected_value: float = required()
    """Current numeric value selected on the slider."""

    step: float = 1.0
    """Increment step between selectable values."""

    horizontal: bool = True
    """True when the slider is horizontal; False for vertical."""

    min_label: str | None = None
    """Label shown for the minimum value."""

    max_label: str | None = None
    """Label shown for the maximum value."""

    def init(self) -> None:
        if isinstance(self.selected_value, int):
            self.selected_value = float(self.selected_value)

    def get_control_type(self) -> str:
        return SliderControl.__name__
