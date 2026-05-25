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

from __future__ import annotations
from dataclasses import dataclass
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.records.interactive_mixin import InteractiveMixin
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.ui.control import Control
from cl.runtime.ui.event.record_update_event import RecordUpdateEvent
from cl.runtime.ui.event.ui_event import UiEvent
from cl.runtime.ui.event.ui_event_handler import UiEventHandler


@dataclass(slots=True, kw_only=True)
class RecordUpdateEventHandler(UiEventHandler[RecordUpdateEvent]):
    def process(self, target: Control | InteractiveMixin, event: RecordUpdateEvent) -> list[UiEvent]:
        """Forward the candidate record to `target.update_record()` without persisting it.

        The candidate is deserialized while still mutable so `update_record()` can also
        normalize or derive fields. The returned list of UiEvent objects is forwarded to the
        frontend as is:

        - On full success: a single `RecordUpdateEvent` with the normalized candidate.
        - On any failure: one `UserErrorEvent` per failing field, optionally followed by a
          `RecordUpdateEvent` carrying the candidate as it stands (un-normalized for failed
          fields).
        """

        if isinstance(target, Control):
            raise UserError("This type of event doesn't work with controls")

        candidate = DataSerializers.FOR_UI.deserialize(event.record)
        if type(candidate) is not type(target):
            raise UserError(
                f"Candidate record type '{type(candidate).__name__}' does not match "
                f"target record type '{type(target).__name__}'."
            )

        return target.update_record(candidate)
