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
from datetime import date
from cl.runtime.ui.control.control import Control


@dataclass(slots=True, kw_only=True, eq=False)
class DateFilterControl(Control):
    """Control for filtering data by date range with the ability to select preset intervals."""

    presets: list[str] | None = None
    """List of available interval presets (e.g. ["1d", "1w", "1m", "3m"])."""

    active_preset: str | None = None
    """Active preset interval, such as "1d", "1w", "3m"."""

    start_date: date | None = None
    """Start filter date."""

    end_date: date | None = None
    """End filter date."""

    @classmethod
    def get_control_type(cls) -> str:
        return DateFilterControl.__name__
