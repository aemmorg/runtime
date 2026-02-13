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
from cl.runtime.ui.control.choice_list_control_item import ChoiceListControlItem
from cl.runtime.ui.control.selectable_control import SelectableControl


@dataclass(slots=True, kw_only=True, eq=False)
class ChoiceListControl(SelectableControl):
    """
    A selectable list control allowing choosing from predefined items.
    Used for single-choice selection.
    """

    selected_index: int | None = None
    """Currently selected item or None if no selection."""

    items: list[ChoiceListControlItem] = required(default_factory=list)
    """List of available selectable items."""

    def get_control_type(self) -> str:
        return ChoiceListControl.__name__
