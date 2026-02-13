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
from typing import Any
from typing import Generator
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.variant import Variant
from cl.runtime.ui.control.core.text_filter import TextFilter
from cl.runtime.ui.control.grid_control import GridControl


@dataclass(slots=True, kw_only=True, eq=False)
class TableControl(GridControl):
    """
    Control representing a table with flattened row-major data storage.
    The data is stored in row-major order.
    """

    data: list[Variant] = required(default_factory=list)
    """Table cells stored row by row in a single list."""

    cell_styles: dict[str, str] | None = None
    """Mapping of cell index (str) identifiers to CSS style strings."""

    col_filters: dict[str, TextFilter] | None = None
    """Per-column filters used by the renderer to restrict visible rows."""

    def init(self) -> None:
        """Initialize the control."""
        # Check that column names are provided
        if not self.col_names:
            raise ValueError("List of column names cannot be empty.")

        # Check that row names are provided and are numeric
        row_names = [str(i) for i in range(self.row_count)]
        if self.row_names and self.row_names != row_names:
            raise ValueError(
                f"Table control can contain only numeric row names. Expected {row_names}, got {self.row_names}",
            )
        elif not self.row_names:
            self.row_names = row_names

        # TODO: Add validation
        # Check that selected row is within bounds, reset to None if not
        if self.selected_row is not None and not (0 <= self.selected_row < self.row_count):
            self.selected_row = None

    @property
    def col_count(self) -> int:
        return len(self.col_names)

    @property
    def row_count(self) -> int:
        return len(self.data or []) // (self.col_count or 1)

    def get_selected_row_data(self) -> Generator[Any, None, None]:
        """Return a generator over the data in the selected row."""
        if self.selected_row is None:
            yield from ()
        else:
            yield from self.get_row_data(row_index=self.selected_row)

    def get_row_data(self, row_index: int | None = None, row_name: str | None = None) -> Generator[Any, None, None]:
        """
        Return a generator over the data in the specified row.

        Args:
            row_index: Zero-based index of the row to retrieve.
            row_name: Name of the row to retrieve, which will be converted to an index if provided.

        If both row_index and row_name are provided, row_name will be used.
        """
        if not self.data:
            yield from ()
            return

        # TODO: Add validation
        if row_name is not None:
            if self.row_names:
                try:
                    row_index = self.row_names.index(row_name)
                except ValueError:
                    raise RuntimeError(f"Row name '{row_name}' is not found.")
            else:
                try:
                    row_index = int(row_name)
                except ValueError:
                    raise RuntimeError(f"Row name must be a string integer, got {row_name}.")
        elif row_index is None:
            raise RuntimeError("Either row index or row name must be specified.")

        if not (0 <= row_index < self.row_count):
            raise RuntimeError(f"Row index {row_index} is out of bounds.")

        start_index = row_index * self.col_count
        end_index = start_index + self.col_count
        for i in range(start_index, end_index):
            yield self.data[i]

    def get_column_data(
        self,
        column_index: int | None = None,
        column_name: str | None = None,
    ) -> Generator[Any, None, None]:
        """
        Return a generator over the data in the specified column.

        Args:
            column_index: Zero-based index of the column to retrieve.
            column_name: Name of the column to retrieve, which will be converted to an index if provided.

        If both column_index and column_name are provided, column_name will be used.
        """
        if not self.data:
            yield from ()
            return

        # TODO: Add validation
        if column_name is not None:
            if self.col_names is None:
                raise RuntimeError("Column names are not defined.")
            try:
                column_index = self.col_names.index(column_name)
            except ValueError:
                raise RuntimeError(f"Column name '{column_name}' is not found.")
        elif column_index is None:
            raise RuntimeError("Either column index or column name must be specified.")

        if not (0 <= column_index < self.col_count):
            raise RuntimeError(f"Column index {column_index} is out of bounds.")

        for i in range(column_index, len(self.data), self.col_count):
            yield self.data[i]

    def get_control_type(self) -> str:
        return TableControl.__name__
