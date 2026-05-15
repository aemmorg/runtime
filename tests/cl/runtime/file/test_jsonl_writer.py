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
import json
import zipfile
from io import BytesIO
from cl.runtime.file.jsonl_writer import JsonlWriter
from cl.runtime.qa.regression_guard import RegressionGuard
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_composite import StubDataclassComposite
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields


def test_jsonl_writer_save_all():
    """Test JsonlWriter.to_files method to generate JSONL files grouped by type.

    Creates records of three different types and verifies that each type
    produces a separate JSONL file with the correct number of records.
    """

    # Create test records of three different types
    derived_records = [
        StubDataclassDerived(id=f"derived_id_{i}", derived_str_field=f"test_derived_str_field_value_{i}").build()
        for i in range(1, 3)
    ]

    nested_records = [StubDataclassNestedFields(id=f"nested_id_{i}").build() for i in range(1, 4)]

    composite_records = [
        StubDataclassComposite(
            primitive=f"nested_primitive_{i}",
            embedded_1=StubDataclassKey(id=f"embedded_key_id_{i}a"),
            embedded_2=StubDataclassKey(id=f"embedded_key_id_{i}b"),
        ).build()
        for i in range(1, 4)
    ]

    all_records = derived_records + nested_records + composite_records

    jsonl_writer = JsonlWriter()
    file_data_list = list(jsonl_writer.to_files(all_records))

    # Sort for consistent ordering
    file_data_list.sort(key=lambda x: x.name)

    # JSONL groups by type, so we should have 3 files (one per type)
    assert len(file_data_list) == 3

    guard = RegressionGuard(prefix="file_structure").build()
    guard.write("JSONL files:")
    for file_data in file_data_list:
        content = file_data.file_bytes.decode("utf-8").replace("\r\n", "\n")
        line_count = len([line for line in content.strip().splitlines() if line.strip()])
        guard.write(f"  - {file_data.name} ({line_count} records)")

    # Verify each file contains valid JSONL
    for file_data in file_data_list:
        content = file_data.file_bytes.decode("utf-8").replace("\r\n", "\n")
        lines = [line for line in content.strip().splitlines() if line.strip()]
        for line in lines:
            json.loads(line)  # Verify each line is valid JSON

        # Write content to regression guard
        channel_name = file_data.name.replace(".jsonl", "")
        guard_for_file = RegressionGuard(prefix=channel_name).build()
        guard_for_file.write(content.rstrip())

    RegressionGuard().verify_all()


def test_jsonl_writer_save_zip():
    """Test JsonlWriter.to_zip method to generate a ZIP file containing JSONL files.

    Verifies that to_zip produces a valid ZIP archive with the expected naming
    convention (Export_*.zip) and that each entry contains valid JSONL content.
    """

    # Create two record types to verify ZIP contains multiple JSONL files
    derived_records = [
        StubDataclassDerived(id=f"derived_id_{i}", derived_str_field=f"test_derived_str_field_value_{i}").build()
        for i in range(1, 3)
    ]

    composite_records = [
        StubDataclassComposite(
            primitive=f"nested_primitive_{i}",
            embedded_1=StubDataclassKey(id=f"embedded_key_id_{i}a"),
            embedded_2=StubDataclassKey(id=f"embedded_key_id_{i}b"),
        ).build()
        for i in range(1, 4)
    ]

    all_records = derived_records + composite_records

    jsonl_writer = JsonlWriter()
    zip_file_data = jsonl_writer.to_zip(all_records)

    guard = RegressionGuard(prefix="zip_structure").build()

    # Read the ZIP from in-memory bytes and verify structure
    zip_buffer = BytesIO(zip_file_data.file_bytes)
    with zipfile.ZipFile(zip_buffer, "r") as zip_archive:
        file_list = sorted(zip_archive.namelist())

        # Verify ZIP file naming convention
        assert zip_file_data.name.startswith("Export_")
        assert zip_file_data.name.endswith(".zip")

        guard.write("Files in ZIP:")
        for file_path in file_list:
            guard.write(f"  - {file_path}")

        # Verify each JSONL file in ZIP
        for file_path in file_list:
            content = zip_archive.read(file_path).decode("utf-8").replace("\r\n", "\n")
            lines = [line for line in content.strip().splitlines() if line.strip()]
            for line in lines:
                json.loads(line)

    RegressionGuard().verify_all()


def test_jsonl_writer_empty_records():
    """Test JsonlWriter with empty records list produces no output files."""

    jsonl_writer = JsonlWriter()

    # to_files should yield nothing for empty input
    file_data_list = list(jsonl_writer.to_files([]))
    assert len(file_data_list) == 0

    # to_zip should produce a valid but empty ZIP archive
    zip_file_data = jsonl_writer.to_zip([])
    zip_buffer = BytesIO(zip_file_data.file_bytes)
    with zipfile.ZipFile(zip_buffer, "r") as zip_archive:
        assert len(zip_archive.namelist()) == 0


def test_jsonl_writer_single_record_type():
    """Test JsonlWriter with records of a single type produces exactly one file."""

    # All records share the same type, so only one JSONL file should be generated
    derived_records = [
        StubDataclassDerived(id=f"test_id_{i}", derived_str_field=f"test_value_{i}").build() for i in range(1, 4)
    ]

    jsonl_writer = JsonlWriter()
    file_data_list = list(jsonl_writer.to_files(derived_records))

    # Should have one file (all same type)
    assert len(file_data_list) == 1

    file_data = file_data_list[0]
    assert file_data.name.endswith(".jsonl")

    # Verify content
    content = file_data.file_bytes.decode("utf-8").replace("\r\n", "\n")
    lines = [line for line in content.strip().splitlines() if line.strip()]
    assert len(lines) == 3

    guard = RegressionGuard(prefix="single_type").build()
    guard.write(f"File: {file_data.name}")
    guard.write(content.rstrip())

    RegressionGuard().verify_all()


def test_jsonl_writer_record_content():
    """Test that JSONL files contain correct serialized record data.

    Verifies that serialized JSON includes _type discriminator and preserves
    all field values from the original record.
    """

    # Create a single record with known field values for content verification
    record = StubDataclassDerived(id="test_content_id", derived_str_field="test_content_value").build()

    jsonl_writer = JsonlWriter()
    file_data_list = list(jsonl_writer.to_files([record]))

    assert len(file_data_list) == 1
    file_data = file_data_list[0]

    # Parse the single JSONL line back to a dict for field-level assertions
    content = file_data.file_bytes.decode("utf-8").replace("\r\n", "\n")
    lines = [line for line in content.strip().splitlines() if line.strip()]
    assert len(lines) == 1

    json_obj = json.loads(lines[0])

    guard = RegressionGuard(prefix="record_content").build()
    guard.write("JSONL content:")
    guard.write(json.dumps(json_obj, indent=2, sort_keys=True))

    # Verify _type discriminator and field values are preserved
    assert "_type" in json_obj
    assert json_obj["id"] == "test_content_id"
    assert json_obj["derived_str_field"] == "test_content_value"

    RegressionGuard().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
