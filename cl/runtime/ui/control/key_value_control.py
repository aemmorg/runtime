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
from cl.runtime.records.variant import Variant
from cl.runtime.ui.control.control_container import ControlContainer
from cl.runtime.ui.control.key_value_cell_control import KeyValueCellControl
from cl.runtime.ui.event.control_event import ControlEvent


@dataclass(slots=True, kw_only=True, eq=False)
class KeyValueControl(ControlContainer):
    """
    Container control holding multiple KeyValueCellControl children.

    Use `set_data` prior to initialization to create child cells from a dict.
    Individual cells are synchronized independently with the frontend.
    """

    def init_content(self):
        """
        This method is intentionally left empty.

        This container has predefined struct and don't need custom one.
        """

    def set_data(self, data: dict):
        """Generate key-value cells according to dict 'data'."""
        for i, (key, value) in enumerate(data.items()):
            cell = KeyValueCellControl(
                key=key,
                value=Variant.create(value),
                control_path=f"{i}",
            )
            self.attach_control(cell)

    def on_change(self, control_path: str, key: str, value: str) -> list[ControlEvent]:
        """Handle change event from a child control."""
        result = []
        if control_path == self.control_path:
            result += self.update_value(key, value)
        if self._parent is not None:
            result += self._parent.on_change(control_path, key, value)
        return result

    def get_control_type(self) -> str:
        return KeyValueControl.__name__
