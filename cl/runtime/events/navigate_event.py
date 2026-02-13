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

from cl.runtime.events.event import Event
from cl.runtime.events.event_kind import EventKind
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class NavigateEvent(Event):
    """Event to trigger navigation to the new target type, record and view in the UI."""

    record_type_name: str = required()
    """Record Type to navigate to."""

    record_key: str | None = None
    """Record key on which to navigate."""

    view_name: str | None = None
    """Name of View to navigate to."""

    view_params: dict[str, str] | None = None
    """View params."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.event_kind is None:
            self.event_kind = EventKind.NAVIGATE
