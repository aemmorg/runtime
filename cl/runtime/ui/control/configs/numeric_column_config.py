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
from cl.runtime.ui.control.configs.column_config import ColumnConfig
from cl.runtime.ui.control.core.formats.negative_number_format import NegativeNumberFormat
from cl.runtime.ui.control.core.formats.numeric_format import NumericFormat


@dataclass(slots=True, kw_only=True)
class NumericColumnConfig(ColumnConfig):
    """Column configuration for numeric values."""

    format: NumericFormat | None = NumericFormat.PLAIN
    """Display format for numbers."""

    negative_number_format: NegativeNumberFormat | None = NegativeNumberFormat.MINUS
    """Display format for negative numbers (minus sign or parentheses)."""

    decimal_places_small: int | None = 6
    """Number of decimal places for values where ABS(value) < 10."""

    decimal_places_medium: int | None = 4
    """Number of decimal places for values where ABS(value) < 1000."""

    decimal_places_large: int | None = 2
    """Number of decimal places for all other values."""

    use_thousands_delimiter: bool | None = True
    """If True, enable thousands separator (e.g., 1,000,000)."""

    min_value: float | None = None
    """Minimum allowed numeric value for editable mode."""

    max_value: float | None = None
    """Maximum allowed numeric value for editable mode."""
