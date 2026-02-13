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
from cl.runtime.ui.control.core.formats.numeric_format import NumericFormat


@dataclass(slots=True, kw_only=True)
class NumericColumnConfig(ColumnConfig):
    """Column configuration for numeric values."""

    format: NumericFormat | None = NumericFormat.PLAIN
    """Display format for numbers."""

    min_value: float | None = None
    """Minimum allowed numeric value for editable mode."""

    max_value: float | None = None
    """Maximum allowed numeric value for editable mode."""
