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
import os
import shutil
from typing import Iterable
from cl.runtime.file.csv_reader import CsvReader
from cl.runtime.file.csv_writer import CsvWriter
from cl.runtime.file.excel_reader import ExcelReader
from cl.runtime.file.excel_writer import ExcelWriter
from cl.runtime.file.json_reader import JsonReader
from cl.runtime.file.json_writer import JsonWriter
from cl.runtime.file.jsonl_reader import JsonlReader
from cl.runtime.file.jsonl_writer import JsonlWriter
from cl.runtime.file.reader import Reader
from cl.runtime.file.writer import Writer
from cl.runtime.file.yaml_reader import YamlReader
from cl.runtime.file.yaml_writer import YamlWriter
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.builder_checks import BuilderChecks
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.yaml_encoders import YamlEncoders
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dict_fields import StubDataclassDictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dict_list_fields import StubDataclassDictListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_empty_fields import StubDataclassEmptyFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_frozendict_fields import StubDataclassFrozendictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_dict_fields import StubDataclassListDictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import StubDataclassListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_numpy_fields import StubDataclassNumpyFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_optional_fields import StubDataclassOptionalFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields import StubDataclassPrimitiveFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_tuple_fields import StubDataclassTupleFields

_YAML_SERIALIZER = DataSerializers.FOR_YAML_SERIALIZATION
_YAML_ENCODER = YamlEncoders.DEFAULT

_SINGLE_RECORD_ENTRIES: list[list[RecordMixin]] = [
    [StubDataclassPrimitiveFields(key_str_field="prim").build()],
    [StubDataclassOptionalFields(id="opt").build()],
    [StubDataclassListFields(id="list").build()],
    [StubDataclassDictFields(id="dict").build()],
    [StubDataclassTupleFields(id="tuple").build()],
    [StubDataclassFrozendictFields(id="fdict").build()],
    [StubDataclassListDictFields(id="ldict").build()],
    [StubDataclassDictListFields(id="dlist").build()],
    [StubDataclassNestedFields(id="nest").build()],
    [StubDataclassEmptyFields(id="empty").build()],
    [StubDataclassNumpyFields(id="numpy").build()],
]

_MULTI_RECORD_ENTRIES: list[list[RecordMixin]] = [
    [StubDataclassPrimitiveFields(key_str_field=f"prim_{i}").build() for i in range(2)],
    [StubDataclassOptionalFields(id=f"opt_{i}").build() for i in range(2)],
    [StubDataclassListFields(id=f"list_{i}").build() for i in range(2)],
    [StubDataclassDictFields(id=f"dict_{i}").build() for i in range(2)],
    [StubDataclassTupleFields(id=f"tuple_{i}").build() for i in range(2)],
    [StubDataclassFrozendictFields(id=f"fdict_{i}").build() for i in range(2)],
    [StubDataclassListDictFields(id=f"ldict_{i}").build() for i in range(2)],
    [StubDataclassDictListFields(id=f"dlist_{i}").build() for i in range(2)],
    [StubDataclassNestedFields(id=f"nest_{i}").build() for i in range(2)],
    [StubDataclassEmptyFields(id=f"empty_{i}").build() for i in range(2)],
    [StubDataclassNumpyFields(id=f"numpy_{i}").build() for i in range(2)],
]

_TESTED_READERS: set[type] = set()
_TESTED_WRITERS: set[type] = set()


def _write_file_data_to_dir(file_data_list, dir_path: str) -> None:
    """Write FileData objects to a directory, creating subdirectories as needed."""
    for file_data in file_data_list:
        if file_data.relative_path:
            target_dir = os.path.join(dir_path, file_data.relative_path)
        else:
            target_dir = dir_path
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, file_data.name)
        with open(file_path, "wb") as f:
            f.write(file_data.file_bytes)


def _save_records_to_yaml(records: Iterable[RecordMixin], file_path: str) -> None:
    """Save records to a YAML file as a YAML list."""
    record_dicts = [_YAML_SERIALIZER.serialize(rec) for rec in records]
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, mode="w", encoding="utf-8") as f:
        yaml_str = _YAML_ENCODER.encode(record_dicts)
        f.write(yaml_str)


def _clean_work_dir(work_dir: str) -> None:
    """Remove all files and subdirectories in work_dir."""
    for entry in os.listdir(work_dir):
        entry_path = os.path.join(work_dir, entry)
        if os.path.isdir(entry_path):
            shutil.rmtree(entry_path)
        else:
            os.remove(entry_path)


# ── CSV roundtrip ────────────────────────────────────────────────────────────


def test_csv(work_dir_fixture):
    """Test CSV writer-reader roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_READERS.add(CsvReader)
    _TESTED_WRITERS.add(CsvWriter)

    csv_writer = CsvWriter()
    csv_reader = CsvReader().build()

    for entries in _MULTI_RECORD_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)

        file_data_list = list(csv_writer.to_files(entries))
        assert len(file_data_list) == 1
        assert file_data_list[0].name == f"{type_name}.csv"

        temp_path = os.path.join(work_dir_fixture, f"{type_name}.csv")
        with open(temp_path, "wb") as f:
            f.write(file_data_list[0].file_bytes)
        guard = RegressionGuard(prefix=type_name, ext="csv").build()
        guard.register_external_write(temp_path)
        os.remove(temp_path)
        guard.verify()

        loaded = list(
            csv_reader.load_all(
                dirs=[work_dir_fixture],
                ext="csv",
                file_include_patterns=[f"{type_name}.expected.*"],
            ).get("/", ())
        )
        assert BuilderChecks.is_equal(loaded, entries), f"CSV roundtrip failed for {type_name}"


# ── Excel roundtrip ──────────────────────────────────────────────────────────


def test_xlsx(work_dir_fixture):
    """Test Excel writer-reader roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_READERS.add(ExcelReader)
    _TESTED_WRITERS.add(ExcelWriter)

    excel_writer = ExcelWriter()
    excel_reader = ExcelReader().build()

    for entries in _MULTI_RECORD_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)

        file_data_list = list(excel_writer.to_files(entries))
        assert len(file_data_list) == 1
        assert file_data_list[0].name == f"{type_name}.xlsx"

        xlsx_path = os.path.join(work_dir_fixture, file_data_list[0].name)
        with open(xlsx_path, "wb") as f:
            f.write(file_data_list[0].file_bytes)

        loaded = list(
            excel_reader.load_all(
                dirs=[work_dir_fixture],
                ext="xlsx",
                file_include_patterns=[f"{type_name}.*"],
            ).get("/", ())
        )
        assert BuilderChecks.is_equal(loaded, entries), f"XLSX roundtrip failed for {type_name}"

        _clean_work_dir(work_dir_fixture)


# ── JSON roundtrip ───────────────────────────────────────────────────────────


def test_json(work_dir_fixture):
    """Test JSON writer-reader roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_READERS.add(JsonReader)
    _TESTED_WRITERS.add(JsonWriter)

    json_writer = JsonWriter()
    json_reader = JsonReader().build()

    for entries in _SINGLE_RECORD_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)

        file_data_list = list(json_writer.to_files(entries))
        assert len(file_data_list) == 1

        temp_path = os.path.join(work_dir_fixture, f"{type_name}.json")
        with open(temp_path, "wb") as f:
            f.write(file_data_list[0].file_bytes)
        guard = RegressionGuard(prefix=type_name, ext="json").build()
        guard.register_external_write(temp_path)
        os.remove(temp_path)
        guard.verify()

        loaded = list(
            json_reader.load_all(
                dirs=[work_dir_fixture],
                ext="json",
                file_include_patterns=[f"{type_name}.expected.*"],
            ).get("/", ())
        )
        assert BuilderChecks.is_equal(loaded, entries), f"JSON roundtrip failed for {type_name}"


# ── JSONL roundtrip ──────────────────────────────────────────────────────────


def test_jsonl(work_dir_fixture):
    """Test JSONL writer-reader roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_READERS.add(JsonlReader)
    _TESTED_WRITERS.add(JsonlWriter)

    jsonl_writer = JsonlWriter()
    jsonl_reader = JsonlReader().build()

    for entries in _MULTI_RECORD_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)

        file_data_list = list(jsonl_writer.to_files(entries))
        assert len(file_data_list) == 1
        assert file_data_list[0].name == f"{type_name}.jsonl"

        temp_path = os.path.join(work_dir_fixture, f"{type_name}.jsonl")
        with open(temp_path, "wb") as f:
            f.write(file_data_list[0].file_bytes)
        guard = RegressionGuard(prefix=type_name, ext="jsonl").build()
        guard.register_external_write(temp_path)
        os.remove(temp_path)
        guard.verify()

        loaded = list(
            jsonl_reader.load_all(
                dirs=[work_dir_fixture],
                ext="jsonl",
                file_include_patterns=[f"{type_name}.expected.*"],
            ).get("/", ())
        )
        assert BuilderChecks.is_equal(loaded, entries), f"JSONL roundtrip failed for {type_name}"


# ── YAML roundtrip ───────────────────────────────────────────────────────────


def test_yaml(work_dir_fixture):
    """Test YAML writer-reader roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_READERS.add(YamlReader)
    _TESTED_WRITERS.add(YamlWriter)

    yaml_writer = YamlWriter()
    yaml_reader = YamlReader().build()

    # Writer produces single-record files; reader reads them back
    for entries in _SINGLE_RECORD_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)

        file_data_list = list(yaml_writer.to_files(entries))
        assert len(file_data_list) == 1

        temp_path = os.path.join(work_dir_fixture, f"{type_name}.yaml")
        with open(temp_path, "wb") as f:
            f.write(file_data_list[0].file_bytes)
        guard = RegressionGuard(prefix=type_name, ext="yaml").build()
        guard.register_external_write(temp_path)
        os.remove(temp_path)
        guard.verify()

        loaded = list(
            yaml_reader.load_all(
                dirs=[work_dir_fixture],
                ext="yaml",
                file_include_patterns=[f"{type_name}.expected.*"],
            ).get("/", ())
        )
        assert BuilderChecks.is_equal(
            sorted(loaded, key=str), sorted(entries, key=str)
        ), f"YAML single-record roundtrip failed for {type_name}"

    # Multi-record YAML (list format) — tests reader's list parsing
    for entries in _MULTI_RECORD_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)

        temp_path = os.path.join(work_dir_fixture, f"{type_name}Tuple.yaml")
        _save_records_to_yaml(entries, temp_path)
        guard = RegressionGuard(prefix=f"{type_name}Tuple", ext="yaml").build()
        guard.register_external_write(temp_path)
        os.remove(temp_path)
        guard.verify()

        loaded = list(
            yaml_reader.load_all(
                dirs=[work_dir_fixture],
                ext="yaml",
                file_include_patterns=[f"{type_name}Tuple.expected.*"],
            ).get("/", ())
        )
        assert BuilderChecks.is_equal(loaded, entries), f"YAML multi-record roundtrip failed for {type_name}"


# ── YAML scalar roundtrip ────────────────────────────────────────────────────


def test_yaml_scalars(work_dir_fixture):
    """Test YAML encode-decode roundtrip for scalar and tuple values."""

    encoder = YamlEncoders.DEFAULT

    test_cases = {
        "String": ("hello world", ["hello world"]),
        "Float": (3.14, ["3.14"]),
        "StringTuple": (("abc", "def", "ghi"), ["abc", "def", "ghi"]),
        "FloatTuple": ((1.0, 2.5, 3.14), ["1.", "2.5", "3.14"]),
    }

    for prefix, (value, expected_decoded) in test_cases.items():
        yaml_str = encoder.encode(value)

        temp_path = os.path.join(work_dir_fixture, f"{prefix}.yaml")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        guard = RegressionGuard(prefix=prefix, ext="yaml").build()
        guard.register_external_write(temp_path)
        os.remove(temp_path)
        guard.verify()

        expected_path = guard._get_file_path("expected")
        with open(expected_path, "r", encoding="utf-8") as f:
            decoded = encoder.decode(f.read())

        assert decoded == expected_decoded, f"YAML scalar roundtrip failed for {prefix}: {decoded}"


# ── Coverage verification ────────────────────────────────────────────────────


def test_all_readers_and_writers_covered():
    """Verify that every Reader and Writer descendant in the runtime package is tested above."""

    all_readers = set(TypeInfo.get_child_and_self_types(Reader)) - {Reader}
    all_writers = set(TypeInfo.get_child_and_self_types(Writer)) - {Writer}

    missing_readers = all_readers - _TESTED_READERS
    missing_writers = all_writers - _TESTED_WRITERS

    assert (
        not missing_readers
    ), f"Reader subclasses not covered by roundtrip tests: {sorted(c.__name__ for c in missing_readers)}"
    assert (
        not missing_writers
    ), f"Writer subclasses not covered by roundtrip tests: {sorted(c.__name__ for c in missing_writers)}"


if __name__ == "__main__":
    pytest.main([__file__])
