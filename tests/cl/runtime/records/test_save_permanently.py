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

"""Integration tests for UiRecordUtil.run_save_permanently_records method."""

import pytest
import os
import shutil
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.file.file_util import FileUtil
from cl.runtime.records.save_format import SaveFormat
from cl.runtime.records.ui_record_util import UiRecordUtil
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.settings.preload_settings import PreloadSettings
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields


@pytest.mark.parametrize("file_type", [SaveFormat.CSV, SaveFormat.JSON, SaveFormat.YAML], ids=["csv", "json", "yaml"])
def test_save_permanently(default_db_fixture, file_type: SaveFormat):
    """Test run_save_permanently_records saves files to preload directory."""
    ext = file_type.name.lower()
    # Create and save records
    records = [StubDataclass(id=f"perm_save_{i}").build() for i in range(2)] + [
        StubDataclassDerived(id=f"perm_save_derived_{i}").build() for i in range(2)
    ]
    for record in records:
        active(DataSource).replace_one(record, commit=True)

    key_strs = [KeySerializers.DELIMITED.serialize(r.get_key()) for r in records]

    # Run method
    UiRecordUtil.run_save_permanently_records(type_to_save="StubDataclass", keys=key_strs, save_format=file_type)

    # Verify files exist in the expected location
    # Structure: preload_dir/{format}/StubDataclass/id.{ext}
    preload_dir = PreloadSettings.instance().preload_dirs[0]
    if file_type in [SaveFormat.JSON, SaveFormat.YAML]:
        # JSON and YAML both use individual files per record
        for record in records:
            dirname = FileUtil.get_dirname_for_record(record)
            filename = FileUtil.get_filename_for_record(record, ext=ext)
            expected_path = os.path.join(preload_dir, ext, dirname, filename)

            assert os.path.exists(expected_path), f"File not found at expected path: {expected_path}"
            assert os.path.getsize(expected_path) > 0

            # Verify content basic check
            with open(expected_path, "r") as f:
                content = f.read()
                assert record.id in content
    elif file_type == SaveFormat.CSV:
        # CSV uses one file per record type
        for record in records:
            expected_dir = os.path.join(preload_dir, ext)
            record_type = type(record).__name__
            expected_path = os.path.join(expected_dir, f"{record_type}.csv")
            assert os.path.exists(expected_path), f"File not found at expected path: {expected_path}"
            assert os.path.getsize(expected_path) > 0

            # Verify content basic check
            with open(expected_path, "r") as f:
                content = f.read()
                assert record.id in content

    shutil.rmtree(os.path.join(preload_dir, ext))


@pytest.mark.parametrize("file_type", [SaveFormat.JSON, SaveFormat.YAML], ids=["json", "yaml"])
def test_save_permanently_individual_files(default_db_fixture, file_type: SaveFormat):
    """Test that JSON and YAML formats create individual files per record."""
    ext = file_type.name.lower()

    # Create records of different types
    records = [StubDataclass(id=f"individual_test_{i}").build() for i in range(2)] + [
        StubDataclassDerived(id=f"individual_derived_{i}").build() for i in range(2)
    ]

    for record in records:
        active(DataSource).replace_one(record, commit=True)

    key_strs = [KeySerializers.DELIMITED.serialize(r.get_key()) for r in records]

    # Run method
    UiRecordUtil.run_save_permanently_records(type_to_save="StubDataclass", keys=key_strs, save_format=file_type)

    # Verify individual files exist for each record
    preload_dir = PreloadSettings.instance().preload_dirs[0]

    # Track created files to ensure we have the right count
    created_files = []
    for record in records:
        dirname = FileUtil.get_dirname_for_record(record)
        filename = FileUtil.get_filename_for_record(record, ext=ext)
        expected_path = os.path.join(preload_dir, ext, dirname, filename)

        assert os.path.exists(expected_path), f"File not found: {expected_path}"
        assert os.path.getsize(expected_path) > 0, f"Empty file: {expected_path}"
        created_files.append(expected_path)

        # Verify file content contains record ID
        with open(expected_path, "r") as f:
            content = f.read()
            assert record.id in content, f"Record ID not found in {expected_path}"

    # Should have 4 individual files
    assert len(created_files) == 4, f"Expected 4 files, got {len(created_files)}"

    # Cleanup
    shutil.rmtree(os.path.join(preload_dir, ext))


def test_save_permanently_csv_grouped(default_db_fixture):
    """Test that CSV format groups records by type into single files."""

    # Create records of different types
    base_records = [StubDataclass(id=f"csv_base_{i}").build() for i in range(2)]
    derived_records = [StubDataclassDerived(id=f"csv_derived_{i}").build() for i in range(2)]

    all_records = base_records + derived_records

    for record in all_records:
        active(DataSource).replace_one(record, commit=True)

    key_strs = [KeySerializers.DELIMITED.serialize(r.get_key()) for r in all_records]

    # Run method
    UiRecordUtil.run_save_permanently_records(type_to_save="StubDataclass", keys=key_strs, save_format=SaveFormat.CSV)

    # Verify CSV files exist (one per record type)
    preload_dir = PreloadSettings.instance().preload_dirs[0]
    csv_dir = os.path.join(preload_dir, "csv")

    # Should have 2 CSV files: StubDataclass.csv and StubDataclassDerived.csv
    expected_files = [os.path.join(csv_dir, "StubDataclass.csv"), os.path.join(csv_dir, "StubDataclassDerived.csv")]

    for expected_file in expected_files:
        assert os.path.exists(expected_file), f"CSV file not found: {expected_file}"
        assert os.path.getsize(expected_file) > 0, f"Empty CSV file: {expected_file}"

        # Verify CSV content contains relevant record IDs
        with open(expected_file, "r") as f:
            content = f.read()
            if "StubDataclassDerived.csv" in expected_file:
                # Derived CSV should contain derived record IDs
                assert "csv_derived_0" in content or "csv_derived_1" in content
            else:
                # Base CSV should contain all record IDs (base + derived)
                assert "csv_base_0" in content or "csv_derived_0" in content

    # Cleanup
    shutil.rmtree(csv_dir)


@pytest.mark.parametrize("file_type", [SaveFormat.CSV, SaveFormat.JSON, SaveFormat.YAML], ids=["csv", "json", "yaml"])
def test_save_permanently_with_dependencies(default_db_fixture, file_type: SaveFormat):
    """Test save_permanently with dependencies for all formats."""

    # Create dependency record first
    dependency = StubDataclass(id="dependency_record").build()
    active(DataSource).replace_one(dependency, commit=True)

    # Create main record that references the dependency
    main_record = StubDataclassNestedFields(
        id="main_with_deps",
        key_field=StubDataclassKey(id="dependency_record"),
    ).build()
    active(DataSource).replace_one(main_record, commit=True)

    key_str = KeySerializers.DELIMITED.serialize(main_record.get_key())

    # Run with dependencies
    UiRecordUtil.run_save_permanently_records(
        type_to_save="StubDataclassNestedFields", keys=[key_str], save_format=file_type, with_dependencies=True
    )

    # Verify files were created
    preload_dir = PreloadSettings.instance().preload_dirs[0]
    ext = file_type.name.lower()

    if file_type in [SaveFormat.JSON, SaveFormat.YAML]:
        # Should have individual files for both main record and dependency
        main_dirname = FileUtil.get_dirname_for_record(main_record)
        main_filename = FileUtil.get_filename_for_record(main_record, ext=ext)
        main_path = os.path.join(preload_dir, ext, main_dirname, main_filename)

        dep_dirname = FileUtil.get_dirname_for_record(dependency)
        dep_filename = FileUtil.get_filename_for_record(dependency, ext=ext)
        dep_path = os.path.join(preload_dir, ext, dep_dirname, dep_filename)

        assert os.path.exists(main_path), f"Main record file not found: {main_path}"
        assert os.path.exists(dep_path), f"Dependency file not found: {dep_path}"

    elif file_type == SaveFormat.CSV:
        # Should have CSV files for each record type
        csv_dir = os.path.join(preload_dir, ext)
        main_csv = os.path.join(csv_dir, "StubDataclassNestedFields.csv")
        dep_csv = os.path.join(csv_dir, "StubDataclass.csv")

        assert os.path.exists(main_csv), f"Main CSV not found: {main_csv}"
        assert os.path.exists(dep_csv), f"Dependency CSV not found: {dep_csv}"

    # Cleanup
    shutil.rmtree(os.path.join(preload_dir, ext))


@pytest.mark.parametrize("file_type", [SaveFormat.CSV, SaveFormat.JSON, SaveFormat.YAML], ids=["csv", "json", "yaml"])
def test_save_permanently_error_handling(default_db_fixture, file_type: SaveFormat):
    """Test error handling for save_permanently with invalid keys."""

    # Test with non-existent keys
    with pytest.raises(Exception):  # Should raise some form of error when keys don't exist
        UiRecordUtil.run_save_permanently_records(
            type_to_save="StubDataclass", keys=["non_existent_key_123"], save_format=file_type
        )
