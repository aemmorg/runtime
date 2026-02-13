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

from abc import ABC
from dataclasses import dataclass
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.ui.control import Control
from cl.runtime.ui.control.configs.column_config import ColumnConfig
from cl.runtime.ui.control.configs.row_config import RowConfig


@dataclass(slots=True, kw_only=True, eq=False)
class GridControl(Control, ABC):
    """Abstract grid-like control used as the basis for tables and matrices."""

    col_names: list[str] = required(default_factory=list)
    """List of unique column names."""

    row_names: list[str] = required(default_factory=list)
    """List of unique row names."""

    selected_row: int | None = None
    """Index of the selected row, or None when no selection is present."""

    multi_header_separator: str | None = None
    """Separator used to split column and row names into multi-level header parts."""

    col_config: dict[str, ColumnConfig] | None = None
    """Mapping of column name to ColumnConfig."""

    row_config: dict[str, RowConfig] | None = None
    """Mapping of row name to RowConfig."""
