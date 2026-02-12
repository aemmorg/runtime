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

import json
import os
import zipfile
from io import BytesIO
import pytest
from cl.runtime.file.json_writer import JsonWriter
from cl.runtime.qa.regression_guard import RegressionGuard
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_composite import StubDataclassComposite
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields


def test_json_writer_save_all():
    """Test JsonWriter.save_all method to generate JSON files."""

    # Create test data
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

    # Combine all records for testing
    all_records = derived_records + nested_records + composite_records

    # Create JSON writer
    json_writer = JsonWriter()

    # Generate JSON files
    file_data_list = list(json_writer.to_files(all_records))

    # Use RegressionGuard to verify generated JSON files
    guard = RegressionGuard().build()

    # Sort file data by relative_path and name for consistent ordering
    file_data_list.sort(key=lambda x: (x.relative_path or "", x.name))

    # Verify that we have one file per record
    assert len(file_data_list) == len(all_records), f"Expected {len(all_records)} files, got {len(file_data_list)}"

    # Group files by relative_path to verify structure
    files_by_path = {}
    for file_data in file_data_list:
        path = file_data.relative_path or ""
        if path not in files_by_path:
            files_by_path[path] = []
        files_by_path[path].append(file_data)

    # Verify we have the expected folder structure
    guard.write("Folder structure:")
    for path in sorted(files_by_path.keys()):
        file_count = len(files_by_path[path])
        guard.write(f"  {path}/ ({file_count} files)")

    # Verify JSON content for each file
    for file_data in file_data_list:
        # Decode bytes to string
        json_content = file_data.file_bytes.decode("utf-8")

        # Verify it's valid JSON
        json_obj = json.loads(json_content)

        # Write to regression guard with channel name based on the folder and file name
        folder = file_data.relative_path or "root"
        filename_no_ext = file_data.name.replace(".json", "")
        channel_name = f"{folder}_{filename_no_ext}"
        guard_for_file = RegressionGuard(prefix=channel_name).build()
        guard_for_file.write(json_content)

    # Verify all files
    RegressionGuard().verify_all()


def test_json_writer_save_zip():
    """Test JsonWriter.save_zip method to generate a ZIP file containing JSON files in subfolders."""

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

    # Create JSON writer
    json_writer = JsonWriter()

    # Generate ZIP file
    zip_file_data = json_writer.to_zip(all_records)

    # Verify ZIP file structure using RegressionGuard
    guard = RegressionGuard(prefix="zip_structure").build()

    # Extract ZIP contents to examine structure
    zip_buffer = BytesIO(zip_file_data.file_bytes)
    with zipfile.ZipFile(zip_buffer, "r") as zip_archive:
        file_list = sorted(zip_archive.namelist())

        # Verify that the zip file name follows the expected pattern
        assert zip_file_data.name.startswith("Export_")
        assert zip_file_data.name.endswith(".zip")

        # Write normalized file name (timestamp replaced)
        normalized_filename = "Export_YYYYMMDD_HHMMSS_StubDataclass_StubDataclassComposite.zip"
        guard.write(f"ZIP file name: {normalized_filename}")
        guard.write("Files in ZIP (with folder structure):")

        # Group files by folder
        files_by_folder = {}
        for file_path in file_list:
            folder = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            if folder not in files_by_folder:
                files_by_folder[folder] = []
            files_by_folder[folder].append(filename)

        # Write folder structure
        for folder in sorted(files_by_folder.keys()):
            guard.write(f"\n  {folder}/")
            for filename in sorted(files_by_folder[folder]):
                guard.write(f"    - {filename}")

        # Extract and verify contents of each JSON file
        for file_path in file_list:
            json_content = zip_archive.read(file_path).decode("utf-8")

            # Verify it's valid JSON
            json_obj = json.loads(json_content)

            # Create channel name from the file path
            channel_name = f"zip_json_{file_path.replace('/', '_').replace('.json', '')}"
            guard_for_json = RegressionGuard(prefix=channel_name).build()
            guard_for_json.write(json_content)

    # Verify all files
    RegressionGuard().verify_all()


def test_json_writer_empty_records():
    """Test JsonWriter with empty records list."""

    json_writer = JsonWriter()

    # Test save_all with empty list
    file_data_list = list(json_writer.to_files([]))
    assert len(file_data_list) == 0

    # Test save_zip with empty list
    zip_file_data = json_writer.to_zip([])

    # Verify empty ZIP file
    zip_buffer = BytesIO(zip_file_data.file_bytes)
    with zipfile.ZipFile(zip_buffer, "r") as zip_archive:
        assert len(zip_archive.namelist()) == 0


def test_json_writer_single_record_type():
    """Test JsonWriter with records of a single type."""

    # Create test data of single type
    derived_records = [
        StubDataclassDerived(id=f"test_id_{i}", derived_str_field=f"test_value_{i}").build() for i in range(1, 4)
    ]

    json_writer = JsonWriter()

    # Generate JSON files
    file_data_list = list(json_writer.to_files(derived_records))

    # Should have one file per record
    assert len(file_data_list) == 3

    # Verify all files are in the same folder
    folders = set(fd.relative_path for fd in file_data_list)
    assert len(folders) == 1, f"Expected all files in same folder, got {folders}"

    # Verify each file using RegressionGuard
    guard = RegressionGuard(prefix="single_type_structure").build()

    # Sort by filename for consistency
    file_data_list.sort(key=lambda x: x.name)

    folder = file_data_list[0].relative_path
    guard.write(f"All files in folder: {folder}/")
    for file_data in file_data_list:
        guard.write(f"  - {file_data.name}")

        # Verify content
        json_content = file_data.file_bytes.decode("utf-8")
        json_obj = json.loads(json_content)

        # Verify that each JSON has the expected type
        assert "_type" in json_obj
        assert "StubDataclassDerived" in json_obj["_type"]

        # Write content to separate channel
        filename_no_ext = file_data.name.replace(".json", "")
        channel_name = f"single_type_{filename_no_ext}"
        guard_for_file = RegressionGuard(prefix=channel_name).build()
        guard_for_file.write(json_content)

    RegressionGuard().verify_all()


def test_json_writer_file_naming():
    """Test that JSON files are named correctly based on record keys."""

    # Create records with specific keys
    records = [
        StubDataclassDerived(id="simple_key", derived_str_field="test1").build(),
        StubDataclassDerived(id="key_with_special;chars", derived_str_field="test2").build(),
    ]

    json_writer = JsonWriter()
    file_data_list = list(json_writer.to_files(records))

    # Sort for consistent ordering
    file_data_list.sort(key=lambda x: x.name)

    # Verify file naming
    guard = RegressionGuard(prefix="file_naming").build()
    guard.write("File names:")
    for file_data in file_data_list:
        guard.write(f"  - {file_data.name}")
        # Verify it's a valid JSON file
        assert file_data.name.endswith(".json")
        json_content = file_data.file_bytes.decode("utf-8")
        json.loads(json_content)  # Verify valid JSON

    RegressionGuard().verify_all()


def test_json_writer_folder_structure():
    """Test that JSON files are placed in correct folders based on record type."""

    # Create records of different types
    derived_records = [StubDataclassDerived(id=f"id_{i}", derived_str_field=f"value_{i}").build() for i in range(2)]
    composite_records = [
        StubDataclassComposite(
            primitive=f"prim_{i}",
            embedded_1=StubDataclassKey(id=f"key_{i}a"),
            embedded_2=StubDataclassKey(id=f"key_{i}b"),
        ).build()
        for i in range(2)
    ]

    all_records = derived_records + composite_records

    json_writer = JsonWriter()
    file_data_list = list(json_writer.to_files(all_records))

    # Group by folder
    files_by_folder = {}
    for file_data in file_data_list:
        folder = file_data.relative_path or "root"
        if folder not in files_by_folder:
            files_by_folder[folder] = []
        files_by_folder[folder].append(file_data.name)

    # Verify folder structure
    guard = RegressionGuard(prefix="folder_structure").build()
    guard.write("Folder structure:")
    for folder in sorted(files_by_folder.keys()):
        guard.write(f"\n{folder}/")
        for filename in sorted(files_by_folder[folder]):
            guard.write(f"  - {filename}")

    # Verify we have multiple folders
    assert len(files_by_folder) > 1, "Expected files in multiple folders"

    RegressionGuard().verify_all()


def test_json_writer_record_content():
    """Test that JSON files contain correct serialized record data."""

    # Create a record with known data
    record = StubDataclassDerived(id="test_content_id", derived_str_field="test_content_value").build()

    json_writer = JsonWriter()
    file_data_list = list(json_writer.to_files([record]))

    assert len(file_data_list) == 1
    file_data = file_data_list[0]

    # Parse JSON content
    json_content = file_data.file_bytes.decode("utf-8")
    json_obj = json.loads(json_content)

    # Verify content structure
    guard = RegressionGuard(prefix="record_content").build()
    guard.write("JSON content:")
    guard.write(json.dumps(json_obj, indent=2, sort_keys=True))

    # Verify key fields are present
    assert "_type" in json_obj
    assert "id" in json_obj
    assert json_obj["id"] == "test_content_id"
    assert "derived_str_field" in json_obj
    assert json_obj["derived_str_field"] == "test_content_value"

    RegressionGuard().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
