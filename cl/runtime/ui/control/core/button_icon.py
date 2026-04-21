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

from enum import auto
from enum import IntEnum


class ButtonIcon(IntEnum):
    """Button icons."""

    REFRESH = auto()
    """Refresh icon."""

    SUCCESS = auto()
    """Success icon."""

    ERROR = auto()
    """Error icon."""

    INFO = auto()
    """Info icon."""

    BELL = auto()
    """Bell icon."""

    ADD = auto()
    """Add icon."""

    DELETE = auto()
    """Delete icon."""

    ARROW_DOWN = auto()
    """Arrow Down icon."""

    ARROW_UP = auto()
    """Arrow Up icon."""

    THUMB_UP = auto()
    """Thumb Up icon."""

    THUMB_DOWN = auto()
    """Thumb Down icon."""
