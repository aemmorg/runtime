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
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.ui.event.control_event import ControlEvent


@dataclass(slots=True, kw_only=True)
class PartialValueUpdateEvent(ControlEvent):
    """Event for updating part of single field of the Control, needs for complex controls."""

    key: str = required()
    "Name of the control field whose part was changed."

    value: Any = required()
    "New value for part of the control field."

    index: str = required()
    "Index for the part of the control field that was changed."
