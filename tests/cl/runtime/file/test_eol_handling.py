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
from cl.runtime.file.csv_reader import CsvReader
from cl.runtime.file.csv_writer import CsvWriter
from cl.runtime.file.json_reader import JsonReader
from cl.runtime.file.json_writer import JsonWriter
from cl.runtime.file.jsonl_reader import JsonlReader
from cl.runtime.file.jsonl_writer import JsonlWriter
from cl.runtime.file.yaml_reader import YamlReader
from cl.runtime.file.yaml_writer import YamlWriter
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived

_SAMPLE_RECORDS = [StubDataclassDerived(id=f"eol_id_{i}", derived_str_field=f"value_{i}").build() for i in range(1, 4)]
"""Three sample records used by all EOL tests."""


def _assert_no_cr_in_fields(records):
    """Assert that no deserialized field value contains a carriage return character."""
    for record in records:
        assert "\r" not in record.id, f"CR found in id field: {record.id!r}"
        assert "\r" not in record.derived_str_field, f"CR found in derived_str_field: {record.derived_str_field!r}"


# ---------------------------------------------------------------------------
#  CSV
# ---------------------------------------------------------------------------

_CSV_LF = "Id,DerivedStrField\neol_id_1,value_1\neol_id_2,value_2\neol_id_3,value_3\n"
_CSV_CRLF = _CSV_LF.replace("\n", "\r\n")


def test_csv_reader_accepts_lf(tmp_path):
    """CsvReader can read a CSV file that uses LF line endings."""
    csv_path = tmp_path / "StubDataclassDerived.csv"
    csv_path.write_bytes(_CSV_LF.encode("utf-8"))

    records = list(CsvReader().build().load_all(dirs=[str(tmp_path)], ext="csv").get("/", ()))
    assert len(records) == 3
    _assert_no_cr_in_fields(records)
    assert records[0].id == "eol_id_1"


def test_csv_reader_accepts_crlf(tmp_path):
    """CsvReader can read a CSV file that uses CRLF line endings."""
    csv_path = tmp_path / "StubDataclassDerived.csv"
    csv_path.write_bytes(_CSV_CRLF.encode("utf-8"))

    records = list(CsvReader().build().load_all(dirs=[str(tmp_path)], ext="csv").get("/", ()))
    assert len(records) == 3
    _assert_no_cr_in_fields(records)
    assert records[0].id == "eol_id_1"


def test_csv_writer_uses_os_linesep():
    """CsvWriter produces bytes with OS-specific line endings."""
    file_data_list = list(CsvWriter().build().to_files(_SAMPLE_RECORDS))
    assert len(file_data_list) == 1

    raw = file_data_list[0].file_bytes
    text = raw.decode("utf-8")

    # Must contain OS-native line endings
    assert os.linesep in text
    # Must NOT contain the opposite style
    if os.linesep == "\r\n":
        # On Windows: every \n must be preceded by \r
        assert "\n" in text  # \r\n contains \n
        bare_lf = text.replace("\r\n", "").count("\n")
        assert bare_lf == 0, f"Found {bare_lf} bare LF(s) on Windows"
    else:
        # On Unix: no \r should appear
        assert "\r" not in text


# ---------------------------------------------------------------------------
#  JSON
# ---------------------------------------------------------------------------

_JSON_LF = (
    "[\n"
    "  {\n"
    '    "_type": "StubDataclassDerived",\n'
    '    "derived_str_field": "value_1",\n'
    '    "id": "eol_id_1"\n'
    "  },\n"
    "  {\n"
    '    "_type": "StubDataclassDerived",\n'
    '    "derived_str_field": "value_2",\n'
    '    "id": "eol_id_2"\n'
    "  },\n"
    "  {\n"
    '    "_type": "StubDataclassDerived",\n'
    '    "derived_str_field": "value_3",\n'
    '    "id": "eol_id_3"\n'
    "  }\n"
    "]"
)
_JSON_CRLF = _JSON_LF.replace("\n", "\r\n")


def test_json_reader_accepts_lf(tmp_path):
    """JsonReader can read a JSON file that uses LF line endings."""
    json_path = tmp_path / "StubDataclassDerived.json"
    json_path.write_bytes(_JSON_LF.encode("utf-8"))

    records = list(JsonReader().build().load_all(dirs=[str(tmp_path)], ext="json").get("/", ()))
    assert len(records) == 3
    _assert_no_cr_in_fields(records)
    assert records[0].id == "eol_id_1"


def test_json_reader_accepts_crlf(tmp_path):
    """JsonReader can read a JSON file that uses CRLF line endings."""
    json_path = tmp_path / "StubDataclassDerived.json"
    json_path.write_bytes(_JSON_CRLF.encode("utf-8"))

    records = list(JsonReader().build().load_all(dirs=[str(tmp_path)], ext="json").get("/", ()))
    assert len(records) == 3
    _assert_no_cr_in_fields(records)
    assert records[0].id == "eol_id_1"


def test_json_writer_uses_os_linesep():
    """JsonWriter produces bytes with OS-specific line endings."""
    file_data_list = list(JsonWriter().build().to_files(_SAMPLE_RECORDS))
    assert len(file_data_list) == 3  # one file per record

    for file_data in file_data_list:
        raw = file_data.file_bytes
        text = raw.decode("utf-8")

        assert os.linesep in text
        if os.linesep == "\r\n":
            bare_lf = text.replace("\r\n", "").count("\n")
            assert bare_lf == 0, f"Found {bare_lf} bare LF(s) on Windows in {file_data.name}"
        else:
            assert "\r" not in text


# ---------------------------------------------------------------------------
#  JSONL
# ---------------------------------------------------------------------------

_JSONL_LF = (
    '{"_type":"StubDataclassDerived","derived_str_field":"value_1","id":"eol_id_1"}\n'
    '{"_type":"StubDataclassDerived","derived_str_field":"value_2","id":"eol_id_2"}\n'
    '{"_type":"StubDataclassDerived","derived_str_field":"value_3","id":"eol_id_3"}\n'
)
_JSONL_CRLF = _JSONL_LF.replace("\n", "\r\n")


def test_jsonl_reader_accepts_lf(tmp_path):
    """JsonlReader can read a JSONL file that uses LF line endings."""
    jsonl_path = tmp_path / "StubDataclassDerived.jsonl"
    jsonl_path.write_bytes(_JSONL_LF.encode("utf-8"))

    records = list(JsonlReader().build().load_all(dirs=[str(tmp_path)], ext="jsonl").get("/", ()))
    assert len(records) == 3
    _assert_no_cr_in_fields(records)
    assert records[0].id == "eol_id_1"


def test_jsonl_reader_accepts_crlf(tmp_path):
    """JsonlReader can read a JSONL file that uses CRLF line endings."""
    jsonl_path = tmp_path / "StubDataclassDerived.jsonl"
    jsonl_path.write_bytes(_JSONL_CRLF.encode("utf-8"))

    records = list(JsonlReader().build().load_all(dirs=[str(tmp_path)], ext="jsonl").get("/", ()))
    assert len(records) == 3
    _assert_no_cr_in_fields(records)
    assert records[0].id == "eol_id_1"


def test_jsonl_writer_uses_os_linesep():
    """JsonlWriter produces bytes with OS-specific line endings."""
    file_data_list = list(JsonlWriter().build().to_files(_SAMPLE_RECORDS))
    assert len(file_data_list) == 1

    raw = file_data_list[0].file_bytes
    text = raw.decode("utf-8")

    assert os.linesep in text
    if os.linesep == "\r\n":
        bare_lf = text.replace("\r\n", "").count("\n")
        assert bare_lf == 0, f"Found {bare_lf} bare LF(s) on Windows"
    else:
        assert "\r" not in text


# ---------------------------------------------------------------------------
#  YAML
# ---------------------------------------------------------------------------

_YAML_LF = "_type: StubDataclassDerived\n" "derived_str_field: value_1\n" "id: eol_id_1\n"
_YAML_CRLF = _YAML_LF.replace("\n", "\r\n")


def test_yaml_reader_accepts_lf(tmp_path):
    """YamlReader can read a YAML file that uses LF line endings."""
    yaml_path = tmp_path / "StubDataclassDerived.yaml"
    yaml_path.write_bytes(_YAML_LF.encode("utf-8"))

    records = list(YamlReader().build().load_all(dirs=[str(tmp_path)], ext="yaml").get("/", ()))
    assert len(records) == 1
    _assert_no_cr_in_fields(records)
    assert records[0].id == "eol_id_1"


def test_yaml_reader_accepts_crlf(tmp_path):
    """YamlReader can read a YAML file that uses CRLF line endings."""
    yaml_path = tmp_path / "StubDataclassDerived.yaml"
    yaml_path.write_bytes(_YAML_CRLF.encode("utf-8"))

    records = list(YamlReader().build().load_all(dirs=[str(tmp_path)], ext="yaml").get("/", ()))
    assert len(records) == 1
    _assert_no_cr_in_fields(records)
    assert records[0].id == "eol_id_1"


def test_yaml_writer_uses_os_linesep():
    """YamlWriter produces bytes with OS-specific line endings."""
    file_data_list = list(YamlWriter().build().to_files(_SAMPLE_RECORDS))
    assert len(file_data_list) == 3  # one file per record

    for file_data in file_data_list:
        raw = file_data.file_bytes
        text = raw.decode("utf-8")

        assert os.linesep in text
        if os.linesep == "\r\n":
            bare_lf = text.replace("\r\n", "").count("\n")
            assert bare_lf == 0, f"Found {bare_lf} bare LF(s) on Windows in {file_data.name}"
        else:
            assert "\r" not in text


# ---------------------------------------------------------------------------
#  Roundtrip: writer output → reader input
# ---------------------------------------------------------------------------


def test_csv_roundtrip_preserves_records(tmp_path):
    """CsvWriter output can be read back by CsvReader with identical records."""
    # Write
    file_data_list = list(CsvWriter().build().to_files(_SAMPLE_RECORDS))
    for fd in file_data_list:
        (tmp_path / fd.name).write_bytes(fd.file_bytes)

    # Read back
    records = list(CsvReader().build().load_all(dirs=[str(tmp_path)], ext="csv").get("/", ()))
    assert len(records) == 3
    _assert_no_cr_in_fields(records)
    for orig, loaded in zip(_SAMPLE_RECORDS, records):
        assert orig.id == loaded.id
        assert orig.derived_str_field == loaded.derived_str_field


def test_json_roundtrip_preserves_records(tmp_path):
    """JsonWriter output can be read back by JsonReader with identical records."""
    # Write
    file_data_list = list(JsonWriter().build().to_files(_SAMPLE_RECORDS))
    for fd in file_data_list:
        out_dir = tmp_path / fd.relative_path if fd.relative_path else tmp_path
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / fd.name).write_bytes(fd.file_bytes)

    # Read back
    records = list(JsonReader().build().load_all(dirs=[str(tmp_path)], ext="json").get("/", ()))
    assert len(records) == 3
    _assert_no_cr_in_fields(records)
    loaded_by_id = {r.id: r for r in records}
    for orig in _SAMPLE_RECORDS:
        loaded = loaded_by_id[orig.id]
        assert orig.derived_str_field == loaded.derived_str_field


def test_jsonl_roundtrip_preserves_records(tmp_path):
    """JsonlWriter output can be read back by JsonlReader with identical records."""
    # Write
    file_data_list = list(JsonlWriter().build().to_files(_SAMPLE_RECORDS))
    for fd in file_data_list:
        (tmp_path / fd.name).write_bytes(fd.file_bytes)

    # Read back
    records = list(JsonlReader().build().load_all(dirs=[str(tmp_path)], ext="jsonl").get("/", ()))
    assert len(records) == 3
    _assert_no_cr_in_fields(records)
    for orig, loaded in zip(_SAMPLE_RECORDS, records):
        assert orig.id == loaded.id
        assert orig.derived_str_field == loaded.derived_str_field


def test_yaml_roundtrip_preserves_records(tmp_path):
    """YamlWriter output can be read back by YamlReader with identical records."""
    # Write
    file_data_list = list(YamlWriter().build().to_files(_SAMPLE_RECORDS))
    for fd in file_data_list:
        out_dir = tmp_path / fd.relative_path if fd.relative_path else tmp_path
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / fd.name).write_bytes(fd.file_bytes)

    # Read back
    records = list(YamlReader().build().load_all(dirs=[str(tmp_path)], ext="yaml").get("/", ()))
    assert len(records) == 3
    _assert_no_cr_in_fields(records)
    loaded_by_id = {r.id: r for r in records}
    for orig in _SAMPLE_RECORDS:
        loaded = loaded_by_id[orig.id]
        assert orig.derived_str_field == loaded.derived_str_field


if __name__ == "__main__":
    pytest.main([__file__])
