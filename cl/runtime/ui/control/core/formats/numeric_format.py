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

from enum import IntEnum
from enum import auto


class NumericFormat(IntEnum):
    """Rendering options for numeric values."""

    PLAIN = auto()
    """Plain numeric representation (no currency/percent)."""

    PERCENT = auto()
    """Display value as a percentage (e.g., 12.3%)."""

    DOLLAR = auto()
    """Display value formatted as US dollars."""

    EURO = auto()
    """Display value formatted as Euros."""

    COMPACT = auto()
    """Compact human-readable format (e.g., 1.2K, 3.4M)."""

    SCIENTIFIC = auto()
    """Scientific notation (e.g., 1.23e+04)."""
