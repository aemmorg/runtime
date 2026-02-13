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
from cl.runtime.ui.control.control_container import ControlContainer
from cl.runtime.ui.control.core.size_scale import SizeScale


@dataclass(slots=True, kw_only=True, eq=False)
class SidebarControl(ControlContainer):
    """Vertical sidebar container for panels and controls."""

    show_dividers: bool = False
    """When True, draw dividers between sidebar items."""

    gap: SizeScale | None = None
    """Spacing hint between sidebar items."""

    def init_content(self):
        """
        Method for filling the panel with child controls.
        Subclasses should override it to initialize panel content.
        """

    def get_control_type(self) -> str:
        return SidebarControl.__name__
