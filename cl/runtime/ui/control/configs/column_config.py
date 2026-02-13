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
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin


@dataclass(slots=True, kw_only=True)
class ColumnConfig(DataclassMixin):
    """Configuration for an individual table column."""

    label: str | None = None
    """Column header label shown to users."""

    hidden: bool | None = False
    """If True the column should not be visible in the UI."""

    editable: bool = False
    """When True the column supports inline editing in the frontend."""

    width: int | None = None
    """Column width in percent (0-100)."""

    style: str | None = None
    """CSS style string to apply to cells in the column."""
