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

import datetime as dt
import os
import shutil
from typing import Iterable
import orjson
import pandas as pd
import pytest
from openpyxl import Workbook
from cl.runtime.file.csv_reader import CsvReader
from cl.runtime.file.csv_writer import CsvWriter
from cl.runtime.file.excel_reader import ExcelReader
from cl.runtime.file.json_reader import JsonReader
from cl.runtime.file.json_writer import JsonWriter
from cl.runtime.file.jsonl_reader import JsonlReader
from cl.runtime.file.jsonl_writer import JsonlWriter
from cl.runtime.file.reader import Reader
from cl.runtime.file.writer import Writer
from cl.runtime.file.yaml_reader import YamlReader
from cl.runtime.file.yaml_writer import YamlWriter
from cl.runtime.primitive.case_util import CaseUtil
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

_CSV_SERIALIZER = DataSerializers.FOR_CSV
_JSON_SERIALIZER = DataSerializers.FOR_JSON
_YAML_SERIALIZER = DataSerializers.FOR_YAML_SERIALIZATION
_YAML_ENCODER = YamlEncoders.DEFAULT

_STUB_FIELDS_ENTRIES: list[list[RecordMixin]] = [
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


def _save_records_to_csv(records: Iterable, file_path: str) -> None:
    """Save records to a CSV file using the CSV serializer and pandas."""
    record_dicts = []
    for rec in records:
        serialized_record = _CSV_SERIALIZER.serialize(rec)
        serialized_record.pop("_type", None)
        serialized_record = {
            CaseUtil.snake_to_pascal_case_keep_trailing_underscore(k): v for k, v in serialized_record.items()
        }
        record_dicts.append(serialized_record)
    df = pd.DataFrame(record_dicts)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)


def _save_records_to_json(records: Iterable[RecordMixin], file_path: str) -> None:
    """Save records to a JSON file as a JSON array."""
    record_dicts = [_JSON_SERIALIZER.serialize(rec) for rec in records]
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, mode="wb") as f:
        f.write(orjson.dumps(record_dicts, option=orjson.OPT_INDENT_2))


def _save_records_to_jsonl(records: Iterable[RecordMixin], file_path: str) -> None:
    """Save records to a JSONL file, one compact JSON object per line."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, mode="wb") as f:
        for rec in records:
            record_dict = _JSON_SERIALIZER.serialize(rec)
            f.write(orjson.dumps(record_dict) + b"\n")


def _save_records_to_yaml(records: Iterable[RecordMixin], file_path: str) -> None:
    """Save records to a YAML file as a YAML list."""
    record_dicts = [_YAML_SERIALIZER.serialize(rec) for rec in records]
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, mode="w", encoding="utf-8") as f:
        yaml_str = _YAML_ENCODER.encode(record_dicts)
        f.write(yaml_str)


def _parse_compact_datetime(value: str) -> dt.datetime:
    """Parse compact datetime string 'yyyymmdd-hhmmssfff' to datetime object."""
    date_part, time_part = value.split("-")
    return dt.datetime(
        int(date_part[:4]), int(date_part[4:6]), int(date_part[6:8]),
        int(time_part[:2]), int(time_part[2:4]), int(time_part[4:6]),
        int(time_part[6:9]) * 1000,
    )


def _save_records_to_xlsx(records: list[RecordMixin], xlsx_path: str) -> None:
    """Save records to an XLSX file with temporal fields stored as Excel-native types."""
    record_type = type(records[0])
    temporal_fields = ExcelReader._get_temporal_field_types(record_type)

    record_dicts = []
    for rec in records:
        serialized = _CSV_SERIALIZER.serialize(rec)
        serialized.pop("_type", None)
        serialized = {
            CaseUtil.snake_to_pascal_case_keep_trailing_underscore(k): v for k, v in serialized.items()
        }
        record_dicts.append(serialized)

    headers = list(record_dicts[0].keys())

    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(headers)

    for row_dict in record_dicts:
        row = []
        for header in headers:
            value = row_dict.get(header)
            if value is None or value == "":
                row.append("")
                continue
            snake_name = CaseUtil.pascal_to_snake_case(header)
            field_type = temporal_fields.get(snake_name)
            if field_type is dt.date:
                row.append(int(value))
            elif field_type is dt.time:
                row.append(int(value))
            elif field_type is dt.datetime:
                row.append(_parse_compact_datetime(str(value)))
            else:
                row.append(value)
        ws.append(row)

    os.makedirs(os.path.dirname(xlsx_path), exist_ok=True)
    wb.save(xlsx_path)


def _clean_work_dir(work_dir: str) -> None:
    """Remove all files and subdirectories in work_dir."""
    for entry in os.listdir(work_dir):
        entry_path = os.path.join(work_dir, entry)
        if os.path.isdir(entry_path):
            shutil.rmtree(entry_path)
        else:
            os.remove(entry_path)


# ── CSV reader roundtrip ──────────────────────────────────────────────────────


def test_csv_reader_all_fields(work_dir_fixture):
    """Test CsvReader roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_READERS.add(CsvReader)

    for entries in _STUB_FIELDS_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)
        file_path = os.path.join(work_dir_fixture, f"{type_name}.csv")

        _save_records_to_csv(entries, file_path)

        csv_reader = CsvReader().build()
        loaded = list(csv_reader.load_all(
            dirs=[work_dir_fixture],
            ext="csv",
            file_include_patterns=[f"{type_name}.*"],
        ).get("/", ()))

        assert BuilderChecks.is_equal(loaded, entries), f"CSV reader roundtrip failed for {type_name}"

        os.remove(file_path)


# ── CSV writer roundtrip ─────────────────────────────────────────────────────


def test_csv_writer_all_fields(work_dir_fixture):
    """Test CsvWriter write-read roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_WRITERS.add(CsvWriter)

    csv_writer = CsvWriter()

    for entries in _STUB_FIELDS_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)

        file_data_list = list(csv_writer.to_files(entries))
        assert len(file_data_list) == 1, f"Expected 1 CSV file for {type_name}, got {len(file_data_list)}"
        assert file_data_list[0].name == f"{type_name}.csv"

        _write_file_data_to_dir(file_data_list, work_dir_fixture)

        csv_reader = CsvReader().build()
        loaded = list(csv_reader.load_all(
            dirs=[work_dir_fixture],
            ext="csv",
            file_include_patterns=[f"{type_name}.*"],
        ).get("/", ()))

        assert BuilderChecks.is_equal(loaded, entries), f"CSV writer roundtrip failed for {type_name}"

        os.remove(os.path.join(work_dir_fixture, file_data_list[0].name))


# ── Excel reader roundtrip ────────────────────────────────────────────────────


def test_excel_reader_all_fields(work_dir_fixture):
    """Test ExcelReader roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_READERS.add(ExcelReader)

    for entries in _STUB_FIELDS_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)
        xlsx_path = os.path.join(work_dir_fixture, f"{type_name}.xlsx")

        _save_records_to_xlsx(entries, xlsx_path)

        excel_reader = ExcelReader().build()
        loaded = list(excel_reader.load_all(
            dirs=[work_dir_fixture],
            ext="xlsx",
            file_include_patterns=[f"{type_name}.*"],
        ).get("/", ()))

        assert BuilderChecks.is_equal(loaded, entries), f"Excel reader roundtrip failed for {type_name}"

        _clean_work_dir(work_dir_fixture)


# ── JSON reader roundtrip ────────────────────────────────────────────────────


def test_json_reader_all_fields(work_dir_fixture):
    """Test JsonReader roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_READERS.add(JsonReader)

    for entries in _STUB_FIELDS_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)
        file_path = os.path.join(work_dir_fixture, f"{type_name}.json")

        _save_records_to_json(entries, file_path)

        json_reader = JsonReader().build()
        loaded = list(json_reader.load_all(
            dirs=[work_dir_fixture],
            ext="json",
            file_include_patterns=[f"{type_name}.*"],
        ).get("/", ()))

        assert BuilderChecks.is_equal(loaded, entries), f"JSON reader roundtrip failed for {type_name}"

        os.remove(file_path)


# ── JSON writer roundtrip ────────────────────────────────────────────────────


def test_json_writer_all_fields(work_dir_fixture):
    """Test JsonWriter write-read roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_WRITERS.add(JsonWriter)

    json_writer = JsonWriter()

    for entries in _STUB_FIELDS_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)

        file_data_list = list(json_writer.to_files(entries))
        assert len(file_data_list) == len(entries), (
            f"Expected {len(entries)} JSON files for {type_name}, got {len(file_data_list)}"
        )

        _write_file_data_to_dir(file_data_list, work_dir_fixture)

        json_reader = JsonReader().build()
        loaded = list(json_reader.load_all(
            dirs=[work_dir_fixture],
            ext="json",
        ).get("/", ()))

        assert len(loaded) == len(entries), (
            f"JSON writer roundtrip: expected {len(entries)} records for {type_name}, got {len(loaded)}"
        )
        assert BuilderChecks.is_equal(sorted(loaded, key=str), sorted(entries, key=str)), (
            f"JSON writer roundtrip failed for {type_name}"
        )

        _clean_work_dir(work_dir_fixture)


# ── JSONL reader roundtrip ───────────────────────────────────────────────────


def test_jsonl_reader_all_fields(work_dir_fixture):
    """Test JsonlReader roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_READERS.add(JsonlReader)

    for entries in _STUB_FIELDS_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)
        file_path = os.path.join(work_dir_fixture, f"{type_name}.jsonl")

        _save_records_to_jsonl(entries, file_path)

        jsonl_reader = JsonlReader().build()
        loaded = list(jsonl_reader.load_all(
            dirs=[work_dir_fixture],
            ext="jsonl",
            file_include_patterns=[f"{type_name}.*"],
        ).get("/", ()))

        assert BuilderChecks.is_equal(loaded, entries), f"JSONL reader roundtrip failed for {type_name}"

        os.remove(file_path)


# ── JSONL writer roundtrip ───────────────────────────────────────────────────


def test_jsonl_writer_all_fields(work_dir_fixture):
    """Test JsonlWriter write-read roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_WRITERS.add(JsonlWriter)

    jsonl_writer = JsonlWriter()

    for entries in _STUB_FIELDS_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)

        file_data_list = list(jsonl_writer.to_files(entries))
        assert len(file_data_list) == 1, f"Expected 1 JSONL file for {type_name}, got {len(file_data_list)}"
        assert file_data_list[0].name == f"{type_name}.jsonl"

        _write_file_data_to_dir(file_data_list, work_dir_fixture)

        jsonl_reader = JsonlReader().build()
        loaded = list(jsonl_reader.load_all(
            dirs=[work_dir_fixture],
            ext="jsonl",
            file_include_patterns=[f"{type_name}.*"],
        ).get("/", ()))

        assert BuilderChecks.is_equal(loaded, entries), f"JSONL writer roundtrip failed for {type_name}"

        os.remove(os.path.join(work_dir_fixture, file_data_list[0].name))


# ── YAML reader roundtrip ───────────────────────────────────────────────────


def test_yaml_reader_all_fields(work_dir_fixture):
    """Test YamlReader roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_READERS.add(YamlReader)

    for entries in _STUB_FIELDS_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)
        file_path = os.path.join(work_dir_fixture, f"{type_name}.yaml")

        _save_records_to_yaml(entries, file_path)

        yaml_reader = YamlReader().build()
        loaded = list(yaml_reader.load_all(
            dirs=[work_dir_fixture],
            ext="yaml",
            file_include_patterns=[f"{type_name}.*"],
        ).get("/", ()))

        assert BuilderChecks.is_equal(loaded, entries), f"YAML reader roundtrip failed for {type_name}"

        os.remove(file_path)


# ── YAML writer roundtrip ───────────────────────────────────────────────────


def test_yaml_writer_all_fields(work_dir_fixture):
    """Test YamlWriter write-read roundtrip for all Stub*Fields classes (except StubAnyFields)."""

    _TESTED_WRITERS.add(YamlWriter)

    yaml_writer = YamlWriter()

    for entries in _STUB_FIELDS_ENTRIES:
        record_type = type(entries[0])
        type_name = typename(record_type)

        file_data_list = list(yaml_writer.to_files(entries))
        assert len(file_data_list) == len(entries), (
            f"Expected {len(entries)} YAML files for {type_name}, got {len(file_data_list)}"
        )

        _write_file_data_to_dir(file_data_list, work_dir_fixture)

        yaml_reader = YamlReader().build()
        loaded = list(yaml_reader.load_all(
            dirs=[work_dir_fixture],
            ext="yaml",
        ).get("/", ()))

        assert len(loaded) == len(entries), (
            f"YAML writer roundtrip: expected {len(entries)} records for {type_name}, got {len(loaded)}"
        )
        assert BuilderChecks.is_equal(sorted(loaded, key=str), sorted(entries, key=str)), (
            f"YAML writer roundtrip failed for {type_name}"
        )

        _clean_work_dir(work_dir_fixture)


# ── Coverage verification ────────────────────────────────────────────────────


def test_all_readers_and_writers_covered():
    """Verify that every Reader and Writer descendant in the runtime package is tested above."""

    all_readers = set(TypeInfo.get_child_and_self_types(Reader)) - {Reader}
    all_writers = set(TypeInfo.get_child_and_self_types(Writer)) - {Writer}

    missing_readers = all_readers - _TESTED_READERS
    missing_writers = all_writers - _TESTED_WRITERS

    assert not missing_readers, (
        f"Reader subclasses not covered by roundtrip tests: {sorted(c.__name__ for c in missing_readers)}"
    )
    assert not missing_writers, (
        f"Writer subclasses not covered by roundtrip tests: {sorted(c.__name__ for c in missing_writers)}"
    )


if __name__ == "__main__":
    pytest.main([__file__])
