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

import pytest
from dataclasses import dataclass
from typing import Any
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.interactive_mixin import InteractiveMixin
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.ui.event.event_manager import EventManager
from cl.runtime.ui.event.runtime_error_event import RuntimeErrorEvent
from cl.runtime.ui.event.value_update_event import ValueUpdateEvent
from cl.runtime.ui.resolver.record_target_resolver import RecordTargetResolver


@dataclass(slots=True, eq=False)
class StubInteractiveRecordKey(DataclassMixin, KeyMixin):
    id: str = "abc"

    @classmethod
    def get_key_type(cls) -> type[KeyMixin]:
        return StubInteractiveRecordKey


@dataclass(slots=True, kw_only=True)
class StubInteractiveRecord(StubInteractiveRecordKey, RecordMixin, InteractiveMixin):
    value: str | None = None

    def get_key(self) -> StubInteractiveRecordKey:
        return StubInteractiveRecordKey(id=self.id).build()

    def update_value(self, field: str, value: Any) -> list[ValueUpdateEvent]:
        clone = self.clone()
        setattr(clone, field, value)
        active(DataSource).replace_one(clone.build(), commit=True)
        return [ValueUpdateEvent(key=str(self.get_key()), field=field, value=value)]


@dataclass(slots=True, eq=False)
class StubNonInteractiveRecordKey(DataclassMixin, KeyMixin):
    id: str = "abc"

    @classmethod
    def get_key_type(cls) -> type[KeyMixin]:
        return StubNonInteractiveRecordKey


@dataclass(slots=True, kw_only=True)
class StubNonInteractiveRecord(StubNonInteractiveRecordKey, RecordMixin):
    value: str | None = None

    def get_key(self) -> StubNonInteractiveRecordKey:
        return StubNonInteractiveRecordKey(id=self.id).build()


def _register_types():
    TypeInfo.register_type(StubInteractiveRecordKey)
    TypeInfo.register_type(StubInteractiveRecord)
    TypeInfo.register_type(StubNonInteractiveRecordKey)
    TypeInfo.register_type(StubNonInteractiveRecord)


def test_record_value_update(default_db_fixture, type_info_fixture):
    _register_types()
    record = StubInteractiveRecord(id="test_id", value="original").build()
    active(DataSource).replace_one(record, commit=True)

    resolver = RecordTargetResolver(
        key="test_id", type_name="StubInteractiveRecord"
    )
    em = EventManager(resolver=resolver)
    events = em.dispatch(
        {
            "_t": "ValueUpdateEvent",
            "Key": "test_id",
            "Field": "Value",
            "Value": "changed",
        },
    )

    assert len(events) == 1
    assert isinstance(events[0], ValueUpdateEvent)
    assert events[0].value == "changed"

    # Verify persisted
    reloaded = active(DataSource).load_one(StubInteractiveRecordKey(id="test_id").build())
    assert reloaded.value == "changed"


def test_record_resolve_not_interactive(default_db_fixture, type_info_fixture):
    _register_types()
    record = StubNonInteractiveRecord(id="test_id", value="original").build()
    active(DataSource).replace_one(record, commit=True)

    resolver = RecordTargetResolver(
        key="test_id", type_name="StubNonInteractiveRecord"
    )
    em = EventManager(resolver=resolver)
    events = em.dispatch(
        {
            "_t": "ValueUpdateEvent",
            "Key": "test_id",
            "Field": "Value",
            "Value": "changed",
        },
    )

    assert len(events) == 1
    assert isinstance(events[0], RuntimeErrorEvent)
    assert "InteractiveMixin" in events[0].error


def test_record_resolve_missing_key(default_db_fixture, type_info_fixture):
    _register_types()

    resolver = RecordTargetResolver(
        key="nonexistent", type_name="StubInteractiveRecord"
    )
    em = EventManager(resolver=resolver)
    events = em.dispatch(
        {
            "_t": "ValueUpdateEvent",
            "Key": "nonexistent",
            "Field": "Value",
            "Value": "changed",
        },
    )

    assert len(events) == 1
    assert isinstance(events[0], RuntimeErrorEvent)


if __name__ == "__main__":
    pytest.main([__file__])
