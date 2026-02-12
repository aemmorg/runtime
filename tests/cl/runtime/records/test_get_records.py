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

"""Unit tests for UiRecordUtil._get_records method."""

import pytest
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.ui_record_util import UiRecordUtil
from cl.runtime.serializers.key_serializers import KeySerializers
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields


def test_single(default_db_fixture):
    """Test _get_records returns a single record when keys contain one element."""

    # Create and save a record
    record = StubDataclass(id="test_single_1").build()
    active(DataSource).replace_one(record, commit=True)

    # Get the serialized key
    key_str = KeySerializers.DELIMITED.serialize(record.get_key())

    # Fetch records using _get_records
    result = UiRecordUtil._get_records(
        type_to_export="StubDataclass",
        keys=[key_str],
        with_dependencies=False,
    )

    # Assert
    assert len(result) == 1
    assert result[0].id == "test_single_1"


def test_multi(default_db_fixture):
    """Test _get_records returns multiple records when keys contain multiple elements."""

    # Create and save multiple records
    records = [StubDataclass(id=f"test_multi_{i}").build() for i in range(3)]
    for record in records:
        active(DataSource).replace_one(record, commit=True)

    # Get the serialized keys
    key_strs = [KeySerializers.DELIMITED.serialize(r.get_key()) for r in records]

    # Fetch records using _get_records
    result = UiRecordUtil._get_records(
        type_to_export="StubDataclass",
        keys=key_strs,
        with_dependencies=False,
    )

    # Assert
    assert len(result) == 3
    result_ids = {r.id for r in result}
    expected_ids = {f"test_multi_{i}" for i in range(3)}
    assert result_ids == expected_ids


def test_derived(default_db_fixture):
    """Test _get_records with derived record type."""

    # Create and save a derived record
    record = StubDataclassDerived(id="derived_id_1", derived_str_field="custom").build()
    active(DataSource).replace_one(record, commit=True)

    # Get the serialized key
    key_str = KeySerializers.DELIMITED.serialize(record.get_key())

    # Fetch records using _get_records
    result = UiRecordUtil._get_records(
        type_to_export="StubDataclassDerived",
        keys=[key_str],
        with_dependencies=False,
    )

    # Assert
    assert len(result) == 1
    assert result[0].id == "derived_id_1"
    assert result[0].derived_str_field == "custom"


def test_dedup(default_db_fixture):
    """Test _get_records removes duplicate keys."""

    # Create and save a record
    record = StubDataclass(id="test_dup_1").build()
    active(DataSource).replace_one(record, commit=True)

    # Get the serialized key
    key_str = KeySerializers.DELIMITED.serialize(record.get_key())

    # Fetch records using _get_records with duplicate keys
    result = UiRecordUtil._get_records(
        type_to_export="StubDataclass",
        keys=[key_str, key_str, key_str],  # duplicates
        with_dependencies=False,
    )

    # Assert
    assert len(result) == 1
    assert result[0].id == "test_dup_1"


def test_with_deps(default_db_fixture):
    """Test _get_records with with_dependencies=True includes dependency records."""

    # Create and save the dependency record first
    dependency_record = StubDataclass(id="dep_record").build()
    active(DataSource).replace_one(dependency_record, commit=True)

    # Create and save a record that has a key field referencing another record
    main_record = StubDataclassNestedFields(
        id="main_record",
        key_field=StubDataclassKey(id="dep_record"),
    ).build()
    active(DataSource).replace_one(main_record, commit=True)

    # Get the serialized key for main record
    key_str = KeySerializers.DELIMITED.serialize(main_record.get_key())

    # Fetch records with dependencies
    result = UiRecordUtil._get_records(
        type_to_export="StubDataclassNestedFields",
        keys=[key_str],
        with_dependencies=True,
    )

    # Assert - should include both the main record and the dependency
    assert len(result) >= 2
    result_ids = {r.id for r in result if hasattr(r, "id")}
    assert "main_record" in result_ids
    assert "dep_record" in result_ids


def test_no_deps(default_db_fixture):
    """Test _get_records with with_dependencies=False does not include dependency records."""

    # Create and save the dependency record first
    dependency_record = StubDataclass(id="dep_only").build()
    active(DataSource).replace_one(dependency_record, commit=True)

    # Create and save a record that has a key field referencing another record
    main_record = StubDataclassNestedFields(
        id="main_only",
        key_field=StubDataclassKey(id="dep_only"),
    ).build()
    active(DataSource).replace_one(main_record, commit=True)

    # Get the serialized key for main record
    key_str = KeySerializers.DELIMITED.serialize(main_record.get_key())

    # Fetch records without dependencies
    result = UiRecordUtil._get_records(
        type_to_export="StubDataclassNestedFields",
        keys=[key_str],
        with_dependencies=False,
    )

    # Assert - should include only the main record
    assert len(result) == 1
    assert result[0].id == "main_only"


if __name__ == "__main__":
    pytest.main([__file__])
