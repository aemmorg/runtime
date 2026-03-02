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

import os
import shutil
from typing import Iterable
import orjson
import pytest
from cl.runtime.file.jsonl_reader import JsonlReader
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.builder_checks import BuilderChecks
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.serializers.data_serializers import DataSerializers
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_composite import StubDataclassComposite
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dict_fields import StubDataclassDictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dict_list_fields import StubDataclassDictListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_double_derived import StubDataclassDoubleDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_dict_fields import StubDataclassListDictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import StubDataclassListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_optional_fields import StubDataclassOptionalFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_other_derived import StubDataclassOtherDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields import StubDataclassPrimitiveFields

_SERIALIZER = DataSerializers.FOR_JSON
"""Serializer for JSON serialization."""

# Each inner list contains 5 records of the same type, covering various field configurations
stub_entries: list[list[RecordMixin]] = [  # noqa
    [StubDataclass(id=f"abc1_n{i}").build() for i in range(5)],
    [StubDataclassNestedFields(id=f"abc2_n{i}").build() for i in range(5)],
    [StubDataclassComposite(primitive=f"abc{i}").build() for i in range(5)],
    [StubDataclassDerived(id=f"abc3_n{i}").build() for i in range(5)],
    [StubDataclassDoubleDerived(id=f"abc4_n{i}").build() for i in range(5)],
    [StubDataclassOtherDerived(id=f"abc5_n{i}").build() for i in range(5)],
    [StubDataclassOptionalFields(id=f"abc7_n{i}").build() for i in range(5)],
    [StubDataclassListFields(id=f"abc6_n{i}").build() for i in range(5)],
    [StubDataclassDictFields(id=f"abc8_n{i}").build() for i in range(5)],
    [StubDataclassDictListFields(id=f"abc9_n{i}").build() for i in range(5)],
    [StubDataclassListDictFields(id=f"abc10_n{i}").build() for i in range(5)],
    [StubDataclassPrimitiveFields(key_str_field=f"abc11_n{i}").build() for i in range(5)],
]
"""Stub entries for testing."""


def save_records_to_jsonl(records: Iterable[RecordMixin], file_path: str, *, include_type: bool = True) -> None:
    """Save records to JSONL file, one compact JSON object per line.

    Args:
        records: Records to serialize
        file_path: Output file path (parent directories are created if needed)
        include_type: If True, include _type discriminator field;
                      If False, omit it so the reader must infer the type from the filename
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, mode="wb") as file:
        for rec in records:
            record_dict = _SERIALIZER.serialize(rec)
            if not include_type:
                # Remove _type so roundtrip relies on filename-based type inference
                record_dict.pop("_type", None)
            file.write(orjson.dumps(record_dict) + b"\n")


def test_roundtrip_with_type_field():
    """Test JSONL roundtrip where _type field is included (default serializer behavior).

    Iterates over all stub record types, saves each to JSONL with _type field,
    reads back via JsonlReader, and verifies field-level equality.
    """
    dir_path = QaUtil.get_test_dir_from_call_stack()

    for test_entries in stub_entries:
        try:
            expected_records = test_entries
            record_type = type(expected_records[0])

            # Save to JSONL with _type field
            file_path = os.path.join(dir_path, f"{typename(record_type)}.jsonl")
            save_records_to_jsonl(expected_records, file_path, include_type=True)

            # Load from JSONL
            jsonl_reader = JsonlReader().build()
            record_type_pattern = f"{typename(record_type)}.*"
            records_from_jsonl = jsonl_reader.load_all(
                dirs=[dir_path],
                ext="jsonl",
                file_include_patterns=[record_type_pattern],
            )

            # Verify
            assert BuilderChecks.is_equal(records_from_jsonl, expected_records)
        finally:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)


def test_roundtrip_without_type_field():
    """Test JSONL roundtrip where _type field is omitted, relying on filename for type.

    When _type is absent, JsonlReader infers the record type from the JSONL filename prefix
    (e.g., StubDataclass.*.jsonl -> StubDataclass). This verifies that inference works
    for all stub types.
    """
    dir_path = QaUtil.get_test_dir_from_call_stack()

    for test_entries in stub_entries:
        try:
            expected_records = test_entries
            record_type = type(expected_records[0])

            # Save to JSONL without _type field (relying on filename)
            file_path = os.path.join(dir_path, f"{typename(record_type)}.jsonl")
            save_records_to_jsonl(expected_records, file_path, include_type=False)

            # Load from JSONL - should infer type from filename
            jsonl_reader = JsonlReader().build()
            record_type_pattern = f"{typename(record_type)}.*"
            records_from_jsonl = jsonl_reader.load_all(
                dirs=[dir_path],
                ext="jsonl",
                file_include_patterns=[record_type_pattern],
            )

            # Verify
            assert BuilderChecks.is_equal(records_from_jsonl, expected_records)
        finally:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)


def test_roundtrip_single_record():
    """Test JSONL roundtrip with a single record to verify edge case of one-line file."""
    dir_path = QaUtil.get_test_dir_from_call_stack()

    try:
        expected_record = StubDataclass(id="single_record_test").build()
        record_type = type(expected_record)

        file_path = os.path.join(dir_path, f"{typename(record_type)}.jsonl")
        save_records_to_jsonl([expected_record], file_path, include_type=True)

        jsonl_reader = JsonlReader().build()
        records_from_jsonl = jsonl_reader.load_all(dirs=[dir_path], ext="jsonl")

        assert len(records_from_jsonl) == 1
        assert BuilderChecks.is_equal(records_from_jsonl[0], expected_record)
    finally:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)


def test_roundtrip_mixed_types():
    """Test JSONL roundtrip with mixed types in the same file (using _type field).

    When a single JSONL file contains records of different types (base, derived,
    double-derived), the _type field is required for correct deserialization.
    """
    dir_path = QaUtil.get_test_dir_from_call_stack()

    try:
        # Mix base class and two levels of derived classes in one file
        expected_records = [
            StubDataclass(id="mixed_1").build(),
            StubDataclassDerived(id="mixed_2").build(),
            StubDataclassDoubleDerived(id="mixed_3").build(),
        ]

        # Save with _type field (required when a single file has mixed record types)
        file_path = os.path.join(dir_path, "StubDataclass.jsonl")
        save_records_to_jsonl(expected_records, file_path, include_type=True)

        jsonl_reader = JsonlReader().build()
        records_from_jsonl = jsonl_reader.load_all(dirs=[dir_path], ext="jsonl")

        assert len(records_from_jsonl) == len(expected_records)
        assert BuilderChecks.is_equal(records_from_jsonl, expected_records)
    finally:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)


if __name__ == "__main__":
    pytest.main([__file__])
