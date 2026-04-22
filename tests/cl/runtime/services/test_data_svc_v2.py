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

"""Contract tests for v2.0.0 DataService response shapes.

These tests pin the wire shape the frontend depends on (per docs/api_changes.md).
They fail loudly if the schema surface regresses away from v2.0.0.
"""

import pytest
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.services.data.data_service import DataService
from cl.runtime.services.data.load_record_response import LoadRecordResponse
from cl.runtime.services.data.select_data_response import SelectDataResponse
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived


def test_select_data_response_has_v2_shape(default_db_fixture):
    """SelectDataResponse must expose type_spec/dependencies/query_schemas (not schema_/base_type)."""

    fields = set(SelectDataResponse.model_fields.keys())
    assert fields == {"data", "type_spec", "dependencies", "query_schemas"}


def test_run_select_type_returns_v2_shape(default_db_fixture):
    """run_select_type returns type_spec + dependencies + query_schemas."""

    ds: DataSource = active(DataSource)
    ds.replace_many([StubDataclass(id="a").build(), StubDataclass(id="b").build()], commit=True)

    result = DataService.run_select_type(type_name="StubDataclass")

    # Shape invariants
    assert isinstance(result, SelectDataResponse)
    assert isinstance(result.type_spec, dict) and result.type_spec
    assert isinstance(result.dependencies, dict)
    assert result.query_schemas is None  # develop does not populate query schemas
    # Data rows carry _key / _t
    for row in result.data:
        assert "_t" in row and "_key" in row


def test_run_select_table_returns_v2_shape(default_db_fixture):
    """run_select_table returns type_spec + dependencies + query_schemas."""

    ds: DataSource = active(DataSource)
    ds.replace_many([StubDataclassDerived(id="x").build()], commit=True)

    result = DataService.run_select_table(table_name="StubDataclassKey")

    assert isinstance(result.type_spec, dict) and result.type_spec
    assert isinstance(result.dependencies, dict)
    assert result.query_schemas is None


def test_run_select_accepts_query_dict_kwarg(default_db_fixture):
    """run_select_table/type must accept query_dict kwarg for v2.0.0 compat (ignored in develop)."""

    ds: DataSource = active(DataSource)
    ds.replace_many([StubDataclass(id="q").build()], commit=True)

    # Should not raise on query_dict=None
    DataService.run_select_table(table_name="StubDataclassKey", query_dict=None)
    DataService.run_select_type(type_name="StubDataclass", query_dict=None)


def test_load_record_response_shape():
    """LoadRecordResponse must expose record/type_spec/dependencies."""

    fields = set(LoadRecordResponse.model_fields.keys())
    assert fields == {"record", "type_spec", "dependencies"}


def test_run_load_record_not_found_returns_empty(default_db_fixture):
    """run_load_record returns empty LoadRecordResponse when record not found."""

    key_str = KeySerializers.DELIMITED.serialize(StubDataclass(id="missing").build().get_key())
    result = DataService.run_load_record(type_name="StubDataclass", key=key_str)
    assert isinstance(result, LoadRecordResponse)
    assert result.record is None
    assert result.type_spec is None
    assert result.dependencies is None


def test_run_load_record_found_populates_v2_shape(default_db_fixture):
    """run_load_record returns record + type_spec + dependencies when record exists."""

    ds: DataSource = active(DataSource)
    record = StubDataclass(id="present").build()
    ds.replace_many([record], commit=True)

    key_str = KeySerializers.DELIMITED.serialize(record.get_key())
    result = DataService.run_load_record(type_name="StubDataclass", key=key_str)

    assert result.record is not None
    assert isinstance(result.type_spec, dict) and result.type_spec
    assert isinstance(result.dependencies, dict)


if __name__ == "__main__":
    pytest.main([__file__])
