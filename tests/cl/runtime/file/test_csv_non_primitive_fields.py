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

import csv
import json
import os
import shutil
import tempfile
import pytest
from cl.runtime.file.csv_reader import CsvReader
from cl.runtime.file.csv_writer import CsvWriter
from cl.runtime.records.builder_checks import BuilderChecks
from cl.runtime.records.typename import typename
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dict_fields import StubDataclassDictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dict_list_fields import StubDataclassDictListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import StubDataclassListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields


def _write_file_data_to_dir(file_data_list, dir_path):
    """Write FileData objects to a directory as CSV files."""
    os.makedirs(dir_path, exist_ok=True)
    for file_data in file_data_list:
        file_path = os.path.join(dir_path, file_data.name)
        with open(file_path, "wb") as f:
            f.write(file_data.file_bytes)


def _read_csv_rows(csv_bytes):
    """Parse CSV bytes into a list of row dicts."""
    csv_text = csv_bytes.decode("utf-8")
    reader = csv.DictReader(csv_text.splitlines())
    return list(reader)


def _is_json_str(value):
    """Check if a string is a JSON document or array."""
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if not (stripped.startswith("{") or stripped.startswith("[")):
        return False
    try:
        json.loads(stripped)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def test_nested_fields_csv_format():
    """Test that StubDataclassNestedFields non-primitive fields are written as JSON in single CSV cells."""

    records = [StubDataclassNestedFields(id="n1").build()]
    csv_writer = CsvWriter()
    file_data_list = list(csv_writer.to_files(records))

    assert len(file_data_list) == 1
    rows = _read_csv_rows(file_data_list[0].file_bytes)
    assert len(rows) == 1

    row = rows[0]
    # Nested data fields must be JSON documents in single cells
    for col_name in ("BaseField", "DerivedField", "DoubleDerivedField", "PolymorphicField", "PolymorphicDerivedField"):
        assert col_name in row, f"Column '{col_name}' not found in CSV"
        assert _is_json_str(row[col_name]), (
            f"Column '{col_name}' should contain a JSON document but got: {row[col_name]}"
        )


def test_dict_fields_csv_format():
    """Test that StubDataclassDictFields non-primitive fields are written as JSON in single CSV cells."""

    records = [StubDataclassDictFields(id="d1").build()]
    csv_writer = CsvWriter()
    file_data_list = list(csv_writer.to_files(records))

    assert len(file_data_list) == 1
    rows = _read_csv_rows(file_data_list[0].file_bytes)
    assert len(rows) == 1

    row = rows[0]
    # All dict fields must be JSON documents in single cells
    for col_name in ("StrDict", "FloatDict", "DateDict", "DataDict", "KeyDict", "RecordDict", "DerivedDict"):
        assert col_name in row, f"Column '{col_name}' not found in CSV"
        assert _is_json_str(row[col_name]), (
            f"Column '{col_name}' should contain a JSON document but got: {row[col_name]}"
        )
        # Dict fields must serialize as JSON objects (not arrays)
        assert row[col_name].strip().startswith("{"), (
            f"Column '{col_name}' should be a JSON object but got: {row[col_name]}"
        )


def test_list_fields_csv_format():
    """Test that StubDataclassListFields non-primitive fields are written as JSON in single CSV cells."""

    records = [StubDataclassListFields(id="l1").build()]
    csv_writer = CsvWriter()
    file_data_list = list(csv_writer.to_files(records))

    assert len(file_data_list) == 1
    rows = _read_csv_rows(file_data_list[0].file_bytes)
    assert len(rows) == 1

    row = rows[0]
    # All list fields must be JSON arrays in single cells
    for col_name in ("StrList", "FloatList", "DateList", "DataList", "KeyList", "RecordList", "DerivedList"):
        assert col_name in row, f"Column '{col_name}' not found in CSV"
        assert _is_json_str(row[col_name]), (
            f"Column '{col_name}' should contain a JSON array but got: {row[col_name]}"
        )
        # List fields must serialize as JSON arrays (not objects)
        assert row[col_name].strip().startswith("["), (
            f"Column '{col_name}' should be a JSON array but got: {row[col_name]}"
        )


def test_dict_list_fields_csv_format():
    """Test that StubDataclassDictListFields non-primitive fields are written as JSON in single CSV cells."""

    records = [StubDataclassDictListFields(id="dl1").build()]
    csv_writer = CsvWriter()
    file_data_list = list(csv_writer.to_files(records))

    assert len(file_data_list) == 1
    rows = _read_csv_rows(file_data_list[0].file_bytes)
    assert len(rows) == 1

    row = rows[0]
    # Dict-list fields must be JSON arrays of objects in single cells
    for col_name in ("FloatDictList", "DateDictList", "RecordDictList", "DerivedDictList"):
        assert col_name in row, f"Column '{col_name}' not found in CSV"
        assert _is_json_str(row[col_name]), (
            f"Column '{col_name}' should contain a JSON array but got: {row[col_name]}"
        )
        assert row[col_name].strip().startswith("["), (
            f"Column '{col_name}' should be a JSON array but got: {row[col_name]}"
        )


def test_nested_fields_roundtrip(default_db_fixture):
    """Test write-read-write roundtrip for StubDataclassNestedFields produces no diff."""

    records = [StubDataclassNestedFields(id=f"rt_n{i}").build() for i in range(3)]
    _assert_csv_roundtrip(records)


def test_dict_fields_roundtrip(default_db_fixture):
    """Test write-read-write roundtrip for StubDataclassDictFields produces no diff."""

    records = [StubDataclassDictFields(id=f"rt_d{i}").build() for i in range(3)]
    _assert_csv_roundtrip(records)


def test_list_fields_roundtrip(default_db_fixture):
    """Test write-read-write roundtrip for StubDataclassListFields produces no diff."""

    records = [StubDataclassListFields(id=f"rt_l{i}").build() for i in range(3)]
    _assert_csv_roundtrip(records)


def test_dict_list_fields_roundtrip(default_db_fixture):
    """Test write-read-write roundtrip for StubDataclassDictListFields produces no diff."""

    records = [StubDataclassDictListFields(id=f"rt_dl{i}").build() for i in range(3)]
    _assert_csv_roundtrip(records)


def _assert_csv_roundtrip(records):
    """Assert that write-read-write roundtrip produces identical CSV output."""

    csv_writer = CsvWriter()
    record_type = type(records[0])
    type_name = typename(record_type)

    # First write
    first_write = list(csv_writer.to_files(records))
    assert len(first_write) == 1
    first_csv = first_write[0].file_bytes

    # Write to temp dir, read back with CsvReader
    tmp_dir = tempfile.mkdtemp()
    try:
        _write_file_data_to_dir(first_write, tmp_dir)

        csv_reader = CsvReader().build()
        loaded_records = list(csv_reader.load_all(
            dirs=[tmp_dir],
            ext="csv",
            file_include_patterns=[f"{type_name}*"],
        ).get("/", ()))

        # Verify loaded records match originals
        assert BuilderChecks.is_equal(loaded_records, records), (
            f"Loaded records do not match original records for {type_name}"
        )

        # Second write from loaded records
        second_write = list(csv_writer.to_files(loaded_records))
        assert len(second_write) == 1
        second_csv = second_write[0].file_bytes

        # Compare CSV bytes — no diff allowed
        if first_csv != second_csv:
            first_lines = first_csv.decode("utf-8").splitlines()
            second_lines = second_csv.decode("utf-8").splitlines()
            diffs = []
            for i, (a, b) in enumerate(zip(first_lines, second_lines)):
                if a != b:
                    diffs.append(f"  Line {i + 1}:\n    first:  {a}\n    second: {b}")
            if len(first_lines) != len(second_lines):
                diffs.append(f"  Line count: first={len(first_lines)}, second={len(second_lines)}")
            diff_msg = "\n".join(diffs)
            raise AssertionError(
                f"Write-read-write roundtrip produced different CSV for {type_name}:\n{diff_msg}"
            )
    finally:
        shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    pytest.main([__file__])
