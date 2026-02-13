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
class PanelControl(ControlContainer):
    """Grid-like container where other controls can be placed."""

    col_count: int = 1
    """Number of columns layout supports."""

    row_count: int = 1
    """Number of rows layout supports."""

    row_height: dict[str, int] | None = None
    """Mapping of row index (str) to percents (0-100) describing height."""

    col_width: dict[str, int] | None = None
    """Mapping of column index (str) to percents (0-100) describing width."""

    bordered: bool = True
    """Whether the panel displays a border around its area."""

    show_grid: bool = False
    """When True, child components are visually outlined with grid borders."""

    padding: SizeScale | None = None
    """Padding size for the panel."""

    gap: SizeScale | None = None
    """Gap size between child components."""

    def init_content(self):
        """
        Method for filling the panel with child controls.
        Subclasses should override it to initialize panel content.
        """

    def get_control_type(self) -> str:
        return PanelControl.__name__
