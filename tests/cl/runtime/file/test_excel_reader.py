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
import datetime as dt
import os
import pytest
from openpyxl import Workbook
from cl.runtime.file.excel_reader import ExcelReader

_STUBS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "preloads", "stubs", "cl", "runtime", "file")
)


def test_single_sheet_workbook(work_dir_fixture):
    """Test single-sheet xlsx produces single CSV with correct content."""

    input_filename = "SingleSheetWorkbook.xlsx"
    expected_output_filename = "SingleSheetWorkbook.SingleSheet.csv"
    output_filenames = []
    try:
        output_filenames = ExcelReader._convert_file(input_filename)

        assert len(output_filenames) == 1
        assert os.path.normpath(output_filenames[0]) == expected_output_filename
        assert os.path.exists(expected_output_filename)

        with open(expected_output_filename, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == 2
        assert rows[0]["Id"] == "xlsx_one"
        assert rows[1]["Id"] == "xlsx_two"
    finally:
        for filename in output_filenames:
            if os.path.exists(filename):
                os.remove(filename)


def test_multi_sheet_workbook(work_dir_fixture):
    """Test multi-sheet xlsx produces separate CSVs with normalized sheet names."""

    input_filename = "MultiSheetWorkbook.xlsx"
    expected_output_filenames = [
        "MultiSheetWorkbook.SheetOne.csv",
        "MultiSheetWorkbook.SheetTwo.csv"
    ]
    output_filenames = []
    try:
        output_filenames = ExcelReader._convert_file(input_filename)
        assert output_filenames == expected_output_filenames

        # Check first sheet content
        with open(output_filenames[0], "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert rows[0]["Id"] == "xlsx_multi_sheet_one_a"
        assert rows[1]["Id"] == "xlsx_multi_sheet_one_b"

        # Check second sheet content
        with open(output_filenames[1], "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 1
        assert rows[0]["Id"] == "xlsx_multi_sheet_two_a"
    finally:
        for filename in output_filenames:
            if os.path.exists(filename):
                os.remove(filename)


def test_sheet_name_normalization():
    """Test that sheet names are normalized by removing spaces and invalid filename characters."""

    assert ExcelReader._normalize_sheet_name("Sheet One") == "SheetOne"
    assert ExcelReader._normalize_sheet_name("My:Sheet") == "MySheet"
    assert ExcelReader._normalize_sheet_name('Test"Name') == "TestName"
    assert ExcelReader._normalize_sheet_name("A/B\\C") == "ABC"
    assert ExcelReader._normalize_sheet_name("NoChange") == "NoChange"


def test_sheet_name_collision_detection(work_dir_fixture):
    """Test that normalized sheet name collision raises RuntimeError."""

    input_filename = "SheetNameCollision.xlsx"
    with pytest.raises(RuntimeError, match="Sheet name collision"):
        ExcelReader._convert_file(input_filename)


def test_format_date_field_iso_int():
    """Test date field formatting from iso_int (integer stored in Excel)."""

    assert ExcelReader._format_cell_value(20260315, dt.date) == "20260315"
    assert ExcelReader._format_cell_value(20030501, dt.date) == "20030501"


def test_format_date_field_native_midnight():
    """Test date field formatting from native Excel datetime with midnight time."""

    assert ExcelReader._format_cell_value(dt.datetime(2026, 3, 15), dt.date) == "20260315"
    assert ExcelReader._format_cell_value(dt.datetime(2003, 5, 1, 0, 0, 0), dt.date) == "20030501"


def test_format_date_field_non_midnight_error():
    """Test that date field with non-midnight time component raises RuntimeError."""

    with pytest.raises(RuntimeError, match="non-midnight"):
        ExcelReader._format_cell_value(dt.datetime(2026, 3, 15, 10, 30), dt.date)


def test_format_time_field_iso_int():
    """Test time field formatting from iso_int (integer stored in Excel)."""

    assert ExcelReader._format_cell_value(101530123, dt.time) == "101530123"
    assert ExcelReader._format_cell_value(0, dt.time) == "000000000"
    assert ExcelReader._format_cell_value(235959999, dt.time) == "235959999"


def test_format_time_field_native():
    """Test time field formatting from native time value."""

    assert ExcelReader._format_cell_value(dt.time(10, 15, 30, 123000), dt.time) == "101530123"
    assert ExcelReader._format_cell_value(dt.time(0, 0, 0), dt.time) == "000000000"


def test_format_datetime_field():
    """Test datetime field formatting to iso_str."""

    assert (
        ExcelReader._format_cell_value(dt.datetime(2026, 3, 15, 10, 30, 45, 123000), dt.datetime)
        == "2026-03-15T10:30:45.123Z"
    )
    assert (
        ExcelReader._format_cell_value(dt.datetime(2003, 5, 1, 0, 0, 0), dt.datetime) == "2003-05-01T00:00:00.000Z"
    )


def test_format_datetime_field_wrong_type_error():
    """Test that datetime field with non-datetime value raises RuntimeError."""

    with pytest.raises(RuntimeError, match="Expected native Excel datetime"):
        ExcelReader._format_cell_value(20260315, dt.datetime)


def test_format_none():
    """Test that None values produce empty string regardless of field type."""

    assert ExcelReader._format_cell_value(None, dt.date) == ""
    assert ExcelReader._format_cell_value(None, dt.time) == ""
    assert ExcelReader._format_cell_value(None, dt.datetime) == ""
    assert ExcelReader._format_cell_value(None, None) == ""


def test_format_no_field_type():
    """Test non-temporal fields with no field type use str()."""

    assert ExcelReader._format_cell_value("hello", None) == "hello"
    assert ExcelReader._format_cell_value(42, None) == "42"
    assert ExcelReader._format_cell_value(3.14, None) == "3.14"
    assert ExcelReader._format_cell_value(True, None) == "True"


def test_temporal_field_types():
    """Test _get_temporal_field_types extracts date/time/datetime fields from a record type."""

    from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields import StubDataclassPrimitiveFields

    temporal = ExcelReader._get_temporal_field_types(StubDataclassPrimitiveFields)

    assert temporal["key_date_field"] is dt.date
    assert temporal["key_time_field"] is dt.time
    assert temporal["key_date_time_field"] is dt.datetime
    assert temporal["obj_date_field"] is dt.date
    assert temporal["obj_time_field"] is dt.time
    assert temporal["obj_date_time_field"] is dt.datetime

    # Non-temporal fields should not be present
    assert "key_str_field" not in temporal
    assert "obj_int_field" not in temporal


if __name__ == "__main__":
    pytest.main([__file__])
