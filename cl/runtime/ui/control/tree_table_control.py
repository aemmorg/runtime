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
from cl.runtime.records.variant.data_container import DataContainer
from cl.runtime.ui.control.configs.column_config import ColumnConfig
from cl.runtime.ui.control.control import Control


@dataclass(slots=True, kw_only=True, eq=False)
class TreeTableControl(Control):
    """Table control with columnar data storage and tree-structured rows.

    Data is stored column-by-column: each element of 'data' is a DataContainer
    holding all row values for one column. The first column is typically a
    TreeContainer whose dot-separated entries define the row hierarchy.

    The 'columns' and 'data' lists are parallel — columns[i] configures data[i].
    """

    selected_row: int | None = None
    """Index of the selected row, or None when no selection is present."""

    multi_header_separator: str | None = None
    """Separator used to split column names into multi-level header parts."""

    expand_all: bool = False
    """When True all tree rows are expanded on initial render."""

    columns: list[ColumnConfig] = required(default_factory=list)
    """Column configurations, one per column (parallel to 'data')."""

    data: list[DataContainer] = required(default_factory=list)
    """Column data containers, one per column (parallel to 'columns')."""

    def get_control_type(self) -> str:
        """String representation of control type for serialization."""
        return TreeTableControl.__name__
