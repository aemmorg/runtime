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
from datetime import datetime
from cl.runtime.ui.control.configs.column_config import ColumnConfig
from cl.runtime.ui.control.core.formats.date_time_format import DateTimeFormat


@dataclass(slots=True, kw_only=True)
class DatetimeColumnConfig(ColumnConfig):
    """Column configuration for datetime values."""

    format: DateTimeFormat | None = DateTimeFormat.PLAIN
    """Display format for datetimes."""

    min_value: datetime | None = None
    """Minimum allowed datetime for editable mode."""

    max_value: datetime | None = None
    """Maximum allowed datetime for editable mode."""
