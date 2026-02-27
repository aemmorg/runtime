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
from cl.runtime.contexts.context_manager import active_or_none
from cl.runtime.events.event import Event
from cl.runtime.events.event_kind import EventKind
from cl.runtime.log.task_log import TaskLog


@dataclass(slots=True, kw_only=True)
class RefreshEvent(Event):
    """Event to trigger refresh on UI."""

    record_type_name: str | None = None
    """Record Type on which handler is run."""

    view_name: str | None = None
    """Name of View to refresh."""

    record_key: str | None = None
    """Record key on which handler is run."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        log_context = active_or_none(TaskLog)

        if self.event_kind is None:
            self.event_kind = EventKind.REFRESH

        # Fill in Event fields from Context
        if self.record_type_name is None and log_context is not None:
            self.record_type_name = log_context.record_type_name

        if self.record_key is None and log_context is not None:
            self.record_key = log_context.record_key
