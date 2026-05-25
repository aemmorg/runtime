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
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.ui.event.ui_event import UiEvent
from cl.runtime.ui.event.user_error_event import UserErrorEvent


class InteractiveMixin(DataMixin, ABC):
    """Mixin enabling any Record to send/receive events via WebSocket.

    Provides update_value, update_partial_value, and on_change methods matching
    the Control interface, so existing ValueUpdateEventHandler and
    PartialValueUpdateEventHandler work unchanged via duck typing.

    Works for both existing records (frontend opens an event connection with the
    record's delimited key, and the backend loads it from the DataSource) and
    not-yet-created records (frontend opens the connection with an empty key during
    a creation form flow; ``RecordTargetResolver`` returns a fresh, unbuilt instance
    of the type so user input can be validated via events before anything is
    persisted). Implementations should therefore not assume ``self`` came from the
    DataSource — in the creation case it carries only the dataclass defaults.
    """

    __slots__ = ()

    def update_value(self, field: str, value: Any) -> list[UiEvent]:
        """Update one field, persist to DB, return ValueUpdateEvent."""

        raise NotImplementedError("update_value must be implemented by subclasses if you want to use it.")

    def update_partial_value(self, field: str, value: Any, index: str) -> list[UiEvent]:
        """Update partial field value, persist to DB, return PartialValueUpdateEvent."""

        raise NotImplementedError("update_partial_value must be implemented by subclasses if you want to use it.")

    def update_record(self, candidate: "InteractiveMixin") -> list[UiEvent]:
        """Process a candidate record from the frontend without persisting it.

        Subclasses override this to perform field-level checks and (optionally) normalize
        the candidate. The implementation owns the full response sent back to the frontend:

        - On any failure: return one ``UserErrorEvent`` per failing field (with ``field`` set to
          the PascalCase field name), optionally followed by a ``RecordUpdateEvent`` carrying the
          candidate as it stands (un-normalized for failed fields) so the frontend can rehydrate
          the form with what the user submitted.
        - On full success: return a single ``RecordUpdateEvent`` whose ``record`` is the normalized
          candidate serialized via ``DataSerializers.FOR_UI_DRAFT``.

        The candidate is passed in still mutable (pre-``build()``); implementations may derive
        or normalize fields on it directly and pass it through to
        ``DataSerializers.FOR_UI_DRAFT.serialize(candidate)`` WITHOUT calling ``.build()`` first.
        ``FOR_UI_DRAFT`` uses ``null_inclusion=OMIT``, so required fields are allowed to be
        ``None`` (skipped silently in output) — that is what makes the not-yet-created /
        creation-form path possible. Do not use ``FOR_UI`` here: it requires required-fields to be
        non-None and will crash on partially-filled candidates.

        Implementations must NOT write to the DataSource.
        """

        raise NotImplementedError("update_record must be implemented by subclasses if you want to use it.")

    @staticmethod
    def get_partial_value_type_hint(field_type_hint: TypeHint, index: str, attr: Any) -> TypeHint:
        """Get type hint for part of a field found by index."""
        type_hint = field_type_hint
        for _ in index.split("."):
            type_hint = type_hint.remaining
        return type_hint

    @staticmethod
    def collect_required_field_errors(candidate: "InteractiveMixin") -> list[UserErrorEvent]:
        """Return a UserErrorEvent for each required field on ``candidate`` still set to None.

        Helper for creation-flow ``update_record()``: the frontend may submit partial data
        while the user is still filling out the creation form, and the UI needs to know
        which required fields are missing. Optional fields are skipped. Field names in the
        returned events are PascalCase to match the frontend convention.
        """
        errors: list[UserErrorEvent] = []
        for field_spec in candidate.get_type_spec().fields:
            if field_spec.field_type_hint.optional:
                continue
            if getattr(candidate, field_spec.field_name) is None:
                errors.append(UserErrorEvent(
                    error=f"Field '{field_spec.field_name}' is required.",
                    field=CaseUtil.snake_to_pascal_case(field_spec.field_name),
                ))
        return errors
