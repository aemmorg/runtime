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
from cl.runtime.records.for_dataclasses.extensions import optional
from cl.runtime.ui.control import Control
from cl.runtime.ui.control.configs.button_config import ButtonConfig


@dataclass(slots=True, kw_only=True, eq=False)
class ButtonControl(Control):
    """Represents a clickable button control."""

    pressed: bool = False
    """Whether the button is currently pressed or not."""

    config: ButtonConfig | None = optional(default_factory=ButtonConfig)
    """Optional configuration influencing appearance and behavior."""

    def get_control_type(self) -> str:
        return ButtonControl.__name__
