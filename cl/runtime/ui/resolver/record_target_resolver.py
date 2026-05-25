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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.interactive_mixin import InteractiveMixin
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.ui.resolver.target_resolver import TargetResolver


@dataclass(slots=True, kw_only=True)
class RecordTargetResolver(TargetResolver[InteractiveMixin]):
    """Resolves InteractiveMixin records from a raw delimited key string via DataSource.

    An empty ``key`` represents a not-yet-created record: ``resolve()`` returns a fresh,
    unbuilt instance of the record type so the frontend can validate user input via
    events while the user fills the creation form, before any record is persisted.
    """

    key: str = required()
    """Raw delimited key string. Empty string means the record has not been created yet."""

    type_name: str = required()
    """Record type name (must resolve to an ``InteractiveMixin`` subclass)."""

    _key_obj: KeyMixin | None = None
    """Cached deserialized key, populated on first call when ``key`` is non-empty."""

    def resolve(self, target_id: str) -> InteractiveMixin:
        record_type = TypeInfo.from_type_name(self.type_name)
        if not issubclass(record_type, InteractiveMixin):
            raise RuntimeError(f"Type {self.type_name} does not implement InteractiveMixin")

        if not self.key:
            # Not-yet-created record: return a fresh, unbuilt instance per call so handlers
            # may mutate it freely without state leaking between events.
            return record_type()

        return active(DataSource).load_one(self._ensure_key_obj(record_type))

    def _ensure_key_obj(self, record_type: type) -> KeyMixin:
        """Deserialize ``key`` on first call and cache the result for subsequent dispatches."""
        if self._key_obj is None:
            key_type = record_type.get_key_type()
            self._key_obj = KeySerializers.DELIMITED.deserialize(self.key, TypeHint.for_type(key_type)).build()
        return self._key_obj
