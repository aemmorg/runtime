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
import zipfile
from io import BytesIO
from cl.runtime.file.csv_writer import CsvWriter
from cl.runtime.qa.regression_guard import RegressionGuard
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_composite import StubDataclassComposite
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields


def test_csv_writer_save_all():
    """Test CsvWriter.save_all method to generate CSV files."""

    # Create test data
    derived_records = [
        StubDataclassDerived(id=f"derived_id_{i}", derived_str_field=f"test_derived_str_field_value_{i}").build()
        for i in range(1, 3)
    ]

    nested_records = [StubDataclassNestedFields().build() for _ in range(1, 4)]

    composite_records = [
        StubDataclassComposite(
            primitive=f"nested_primitive_{i}",
            embedded_1=StubDataclassKey(id=f"embedded_key_id_{i}a"),
            embedded_2=StubDataclassKey(id=f"embedded_key_id_{i}b"),
        ).build()
        for i in range(1, 4)
    ]

    # Combine all records for testing
    all_records = derived_records + nested_records + composite_records

    # Create CSV writer
    csv_writer = CsvWriter()

    # Generate CSV files
    file_data_list = list(csv_writer.to_files(all_records))

    # Use RegressionGuard to verify generated CSV files
    guard = RegressionGuard().build()

    # Sort file data by name for consistent ordering
    file_data_list.sort(key=lambda x: x.name)

    for file_data in file_data_list:
        # Decode bytes to string for text comparison
        csv_content = file_data.file_bytes.decode("utf-8").replace("\r\n", "\n")

        # Write to regression guard with channel name based on the file name
        channel_name = file_data.name.replace(".csv", "")
        guard_for_file = RegressionGuard(prefix=channel_name).build()
        guard_for_file.write(csv_content)

    # Verify all files
    RegressionGuard().verify_all()


def test_csv_writer_save_zip():
    """Test CsvWriter.save_zip method to generate a ZIP file containing CSV files."""

    # Create test data
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

    # Combine records for testing
    all_records = derived_records + composite_records

    # Create CSV writer
    csv_writer = CsvWriter()

    # Generate ZIP file
    zip_file_data = csv_writer.to_zip(all_records)

    # Verify ZIP file structure using RegressionGuard
    guard = RegressionGuard(prefix="zip_contents").build()

    # Extract ZIP contents to examine structure
    zip_buffer = BytesIO(zip_file_data.file_bytes)
    with zipfile.ZipFile(zip_buffer, "r") as zip_archive:
        file_list = sorted(zip_archive.namelist())

        # Verify that the zip file name follows the expected pattern
        assert zip_file_data.name.startswith("Export_")
        assert zip_file_data.name.endswith(".zip")

        # Write file list to regression guard (normalize timestamp in filename)
        normalized_filename = "Export_YYYYMMDD_HHMMSS_StubDataclass_StubDataclassComposite.zip"
        guard.write(f"ZIP file name: {normalized_filename}")
        guard.write("Files in ZIP:")
        for filename in file_list:
            guard.write(f"  - {filename}")

        # Extract and verify contents of each CSV file
        for filename in file_list:
            csv_content = zip_archive.read(filename).decode("utf-8").replace("\r\n", "\n")
            channel_name = f"zip_csv_{filename.replace('.csv', '')}"
            guard_for_csv = RegressionGuard(prefix=channel_name).build()
            guard_for_csv.write(csv_content)

    # Verify all files
    RegressionGuard().verify_all()


def test_csv_writer_empty_records():
    """Test CsvWriter with empty records list."""

    csv_writer = CsvWriter()

    # Test save_all with empty list
    file_data_list = list(csv_writer.to_files([]))
    assert len(file_data_list) == 0

    # Test save_zip with empty list
    zip_file_data = csv_writer.to_zip([])

    # Verify empty ZIP file
    zip_buffer = BytesIO(zip_file_data.file_bytes)
    with zipfile.ZipFile(zip_buffer, "r") as zip_archive:
        assert len(zip_archive.namelist()) == 0


def test_csv_writer_single_record_type():
    """Test CsvWriter with records of a single type."""

    # Create test data of single type
    derived_records = [
        StubDataclassDerived(id=f"test_id_{i}", derived_str_field=f"test_value_{i}").build() for i in range(1, 4)
    ]

    csv_writer = CsvWriter()

    # Generate CSV files
    file_data_list = list(csv_writer.to_files(derived_records))

    # Should have exactly one file
    assert len(file_data_list) == 1
    file_data = file_data_list[0]
    assert file_data.name == "StubDataclassDerived.csv"

    # Verify content using RegressionGuard
    guard = RegressionGuard(prefix="single_type").build()
    csv_content = file_data.file_bytes.decode("utf-8").replace("\r\n", "\n")
    guard.write(csv_content)

    RegressionGuard().verify_all()


def test_csv_writer_error_handling():
    """Test CsvWriter error handling with invalid inputs."""

    csv_writer = CsvWriter()

    # Test None input for save_all
    empty_result = list(csv_writer.to_files(None))
    assert len(empty_result) == 0

    # Test None input for save_zip
    with pytest.raises(RuntimeError, match="Parameter .* is None"):
        csv_writer.to_zip(None)

    # Test with empty list - should return empty iterator (no error)
    empty_result = list(csv_writer.to_files([]))
    assert len(empty_result) == 0

    # Test with list containing None record - should skip None records gracefully
    records_with_none = [
        StubDataclassDerived(id="test", derived_str_field="test").build(),
        None,
        StubDataclassDerived(id="test2", derived_str_field="test2").build(),
    ]

    # Should work without error, just skip None records
    result = list(csv_writer.to_files(records_with_none))
    assert len(result) == 1  # Should have one CSV file with 2 valid records

    # Verify the CSV content has 2 records (header + 2 data rows)
    csv_content = result[0].file_bytes.decode("utf-8").replace("\r\n", "\n")
    csv_lines = csv_content.strip().splitlines()
    assert len(csv_lines) == 3  # header + 2 records


if __name__ == "__main__":
    pytest.main([__file__])
