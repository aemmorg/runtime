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
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.typename import typename
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.ui.event.partial_value_update_event import PartialValueUpdateEvent
from cl.runtime.ui.event.partial_value_update_event_handler import PartialValueUpdateEventHandler
from cl.runtime.ui.event.runtime_error_event import RuntimeErrorEvent
from cl.runtime.ui.event.ui_event import UiEvent
from cl.runtime.ui.event.user_error_event import UserErrorEvent
from cl.runtime.ui.event.value_update_event import ValueUpdateEvent
from cl.runtime.ui.event.value_update_event_handler import ValueUpdateEventHandler
from cl.runtime.ui.resolver.target_resolver import TargetResolver

SUPPORTED_EVENT_HANDLERS = {
    typename(ValueUpdateEvent): ValueUpdateEventHandler,
    typename(PartialValueUpdateEvent): PartialValueUpdateEventHandler,
}


@dataclass(slots=True, kw_only=True)
class EventManager:
    """
    Ensures two-way communication between frontend and database.
    Receives events from frontend via 'dispatch' method and processed them via EventListener.
    Updates from database or backend are send via EventPublisher.
    """

    resolver: TargetResolver = required()
    """Target resolver that determines how to find the target object for incoming events."""

    def dispatch(self, event_dict: dict) -> list[UiEvent]:
        """Process an event received from the frontend.

        Args:
            event_dict: A dictionary representing a UiEvent implementation.
                It must contain the "_t" key with the name of the UiEvent subclass.
                Other keys must match the subclass attributes and their values must conform
                to the corresponding type hints.

                Some attribute values may be dictionaries representing a Variant.
                Such dictionaries must also contain the "_t" key with the name of the
                Variant subclass.

                Examples::

                    {"_t": "ValueUpdateEvent", "Key": "Pressed", "Value": True}
                    {"_t": "PartialValueUpdateEvent", "Key": "Data", "Index": "1",
                       "Value": {"_t": "IntVariant", "Metadata": None, "Value": 12}}

                The method may also receive keep_alive messages from the frontend,
                which do not produce any UiEvent.

        Returns:
            A list of UiEvent objects produced by the dispatch.
        """

        if self._check_for_keep_alive_event(event_dict):
            return []

        target_id = event_dict.get("Key")
        if target_id is None:
            return []

        try:
            # Resolve target object (Control or InteractiveMixin record) by key
            target = self.resolver.resolve(target_id)

            event = BootstrapSerializers.FOR_UI_EVENTS.deserialize(event_dict)

            if event_handler := SUPPORTED_EVENT_HANDLERS.get(typename(type(event))):
                return event_handler().process(target, event)
            else:
                raise RuntimeError(f"Unknown event {event.__class__.__name__}")

        except UserError as e:
            return [UserErrorEvent(key=target_id, error=str(e))]
        except Exception as e:
            return [RuntimeErrorEvent(key=target_id, error=str(e))]

    @staticmethod
    def _check_for_keep_alive_event(event: dict) -> bool:
        return event.get("type", "") == "keep_alive"
