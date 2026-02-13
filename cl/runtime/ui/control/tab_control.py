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
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.ui.control.control import TControl
from cl.runtime.ui.control.control_container import ControlContainer
from cl.runtime.ui.control.panel_control import PanelControl


@dataclass(slots=True, kw_only=True, eq=False)
class TabControl(ControlContainer):
    """
    Container that organizes child panels into tabs.
    Use `create_new_tab` to add a `PanelControl` to a new tab.
    """

    tab_headers: list[str] = required(default_factory=list)
    """Names of the tabs in order."""

    selected_tab: int = 0
    """Index of the currently selected tab (zero-based)."""

    def create_new_tab(self, tab_name: str, control: PanelControl) -> None:
        """
        Create a new tab with a provided control.

        Args:
            tab_name: Name of the tab.
            control: Control to attach to the tab.
        """
        if not isinstance(control, PanelControl):
            raise RuntimeError("To attach a Control to TabControl, it must be an instance of PanelControl.")
        control.control_path = f"tab_{len(self.tab_headers)}"
        self.tab_headers.append(tab_name)
        super(TabControl, self).attach_control(control)

    def attach_control(self, control: TControl) -> None:
        raise UserError("Use create_new_tab method to attach child to the TabControl.")

    def init_content(self):
        """
        Method for filling the tab with child panels.
        Subclasses should override it to initialize tab content.
        """

    def get_control_type(self) -> str:
        return TabControl.__name__
