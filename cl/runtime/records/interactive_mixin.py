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

from abc import ABC
from typing import Any
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.ui.event.ui_event import UiEvent


class InteractiveMixin(DataMixin, ABC):
    """Mixin enabling any Record to send/receive events via WebSocket.

    Provides update_value, update_partial_value, and on_change methods matching
    the Control interface, so existing ValueUpdateEventHandler and
    PartialValueUpdateEventHandler work unchanged via duck typing.
    """

    __slots__ = ()

    def update_value(self, field: str, value: Any) -> list[UiEvent]:
        """Update one field, persist to DB, return ValueUpdateEvent."""

        raise NotImplementedError("update_value must be implemented by subclasses if you want to use it.")

    def update_partial_value(self, field: str, value: Any, index: str) -> list[UiEvent]:
        """Update partial field value, persist to DB, return PartialValueUpdateEvent."""

        raise NotImplementedError("update_partial_value must be implemented by subclasses if you want to use it.")

    @staticmethod
    def get_partial_value_type_hint(field_type_hint: TypeHint, index: str, attr: Any) -> TypeHint:
        """Get type hint for part of a field found by index."""
        type_hint = field_type_hint
        for _ in index.split("."):
            type_hint = type_hint.remaining
        return type_hint
