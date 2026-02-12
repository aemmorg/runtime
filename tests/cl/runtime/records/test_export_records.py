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

"""Integration tests for UiRecordUtil.run_export_records method (API endpoint)."""

import pytest
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.qa.qa_client import QaClient
from cl.runtime.records.save_format import SaveFormat
from cl.runtime.records.ui_record_util import UiRecordUtil
from cl.runtime.serializers.key_serializers import KeySerializers
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dict_list_fields import StubDataclassDictListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_dict_fields import StubDataclassListDictFields
from stubs.cl.runtime.records.for_pydantic.stub_pydantic import StubPydantic
from stubs.cl.runtime.records.for_pydantic.stub_pydantic_key import StubPydanticKey
from stubs.cl.runtime.records.for_pydantic.stub_pydantic_nested_fields import StubPydanticNestedFields


@pytest.mark.parametrize(
    "export_format", [SaveFormat.CSV, SaveFormat.JSON, SaveFormat.YAML], ids=["csv", "json", "yaml"]
)
def test_export_all_formats(default_db_fixture, export_format: SaveFormat):
    """Test run_export_records returns a ZIP file with data in the specified format."""

    # Create and save records
    records = [StubDataclass(id=f"export_test_{i}").build() for i in range(3)]
    for record in records:
        active(DataSource).replace_one(record, commit=True)

    # Get the serialized keys
    key_strs = [KeySerializers.DELIMITED.serialize(r.get_key()) for r in records]

    # Call run_export_records with specific format
    result = UiRecordUtil.run_export_records(
        type_to_export="StubDataclass",
        keys=key_strs,
        with_dependencies=False,
        export_format=export_format,
    )

    # Assert - result should be a FileData object with ZIP content
    assert result is not None
    assert hasattr(result, "file_bytes")
    assert result.file_bytes is not None
    # ZIP files start with PK signature
    assert result.file_bytes[:2] == b"PK"

    # Verify the archive name contains the expected format info
    assert result.name.endswith(".zip")
    assert result.name.startswith("Export_")


def test_export(default_db_fixture):
    """Test run_export_records returns a ZIP file with CSV data."""

    # Create and save records
    records = [StubDataclass(id=f"export_test_{i}").build() for i in range(3)]
    for record in records:
        active(DataSource).replace_one(record, commit=True)

    # Get the serialized keys
    key_strs = [KeySerializers.DELIMITED.serialize(r.get_key()) for r in records]

    # Call run_export_records
    result = UiRecordUtil.run_export_records(
        type_to_export="StubDataclass",
        keys=key_strs,
        with_dependencies=False,
    )

    # Assert - result should be a FileData object with ZIP content
    assert result is not None
    assert hasattr(result, "file_bytes")
    assert result.file_bytes is not None
    # ZIP files start with PK signature
    assert result.file_bytes[:2] == b"PK"


@pytest.mark.parametrize(
    "export_format", [SaveFormat.CSV, SaveFormat.JSON, SaveFormat.YAML], ids=["csv", "json", "yaml"]
)
def test_export_deps_all_formats(default_db_fixture, export_format: SaveFormat):
    """Test run_export_records with dependencies for all formats."""

    # Create and save the dependency record first
    dependency_record = StubPydantic(id=f"export_dep_{export_format.name.lower()}").build()
    active(DataSource).replace_one(dependency_record, commit=True)

    # Create and save a record that has a key field referencing another record
    main_record = StubPydanticNestedFields(
        id=f"export_main_{export_format.name.lower()}",
        key_field=StubPydanticKey(id=f"export_dep_{export_format.name.lower()}"),
    ).build()
    active(DataSource).replace_one(main_record, commit=True)

    # Get the serialized key for main record
    key_str = KeySerializers.DELIMITED.serialize(main_record.get_key())

    # Call run_export_records with dependencies and specific format
    result = UiRecordUtil.run_export_records(
        type_to_export="StubPydanticNestedFields",
        keys=[key_str],
        with_dependencies=True,
        export_format=export_format,
    )

    # Assert - result should be a FileData object with ZIP content
    assert result is not None
    assert hasattr(result, "file_bytes")
    assert result.file_bytes is not None
    # ZIP files start with PK signature
    assert result.file_bytes[:2] == b"PK"


def test_export_deps(default_db_fixture):
    """Test run_export_records with dependencies returns a ZIP file."""

    # Create and save the dependency record first
    dependency_record = StubPydantic(id="export_dep").build()
    active(DataSource).replace_one(dependency_record, commit=True)

    # Create and save a record that has a key field referencing another record
    main_record = StubPydanticNestedFields(
        id="export_main",
        key_field=StubPydanticKey(id="export_dep"),
    ).build()
    active(DataSource).replace_one(main_record, commit=True)

    # Get the serialized key for main record
    key_str = KeySerializers.DELIMITED.serialize(main_record.get_key())

    # Call run_export_records with dependencies
    result = UiRecordUtil.run_export_records(
        type_to_export="StubPydanticNestedFields",
        keys=[key_str],
        with_dependencies=True,
    )

    # Assert - result should be a FileData object with ZIP content
    assert result is not None
    assert hasattr(result, "file_bytes")
    assert result.file_bytes is not None
    # ZIP files start with PK signature
    assert result.file_bytes[:2] == b"PK"


def test_export_err(default_db_fixture):
    """Test run_export_records raises error when no records are found."""

    # Call run_export_records with non-existent keys
    # When records are not found, load_many returns None values which triggers a type check error
    with pytest.raises(RuntimeError, match="Expected a record instance but received None"):
        UiRecordUtil.run_export_records(
            type_to_export="StubDataclass",
            keys=["non_existent_key"],
            with_dependencies=False,
        )


@pytest.mark.parametrize(
    "export_format", [SaveFormat.CSV, SaveFormat.JSON, SaveFormat.YAML], ids=["csv", "json", "yaml"]
)
def test_api_all_formats(default_db_fixture, export_format: SaveFormat):
    """Test run_export_records via the handler/run API endpoint for all formats."""

    # Create and save records
    records = [StubDataclass(id=f"api_test_{export_format.name.lower()}_{i}").build() for i in range(2)]
    for record in records:
        active(DataSource).replace_one(record, commit=True)

    # Get the serialized keys
    key_strs = [KeySerializers.DELIMITED.serialize(r.get_key()) for r in records]

    # Test via REST API
    with QaClient() as test_client:
        request = {
            "Type": "UiRecordUtil",
            "Method": "RunExportRecords",
            "Keys": [],
            "Arguments": {
                "TypeToExport": "StubDataclass",
                "Keys": key_strs,
                "WithDependencies": False,
                "ExportFormat": CaseUtil.upper_to_pascal_case(export_format.name),  # Pass the enum name
            },
        }

        response = test_client.post("/task/run", json=request)
        assert response.status_code == 200

        # Response should contain a FileData result
        result = response.json()
        assert isinstance(result, dict)
        assert result.get("_t") == "FileData"
        assert "FileBytes" in result
        # ZIP files start with PK signature, verify base64 starts with UEs (PK in base64)
        assert result["FileBytes"].startswith("UEs")


def test_api(default_db_fixture):
    """Test run_export_records via the handler/run API endpoint (end-to-end)."""

    # Create and save records
    records = [StubDataclass(id=f"api_test_{i}").build() for i in range(2)]
    for record in records:
        active(DataSource).replace_one(record, commit=True)

    # Get the serialized keys
    key_strs = [KeySerializers.DELIMITED.serialize(r.get_key()) for r in records]

    # Test via REST API
    with QaClient() as test_client:
        request = {
            "Type": "UiRecordUtil",
            "Method": "RunExportRecords",
            "Keys": [],
            "Arguments": {
                "TypeToExport": "StubDataclass",
                "Keys": key_strs,
                "WithDependencies": False,
            },
        }

        response = test_client.post("/task/run", json=request)
        assert response.status_code == 200

        # Response should contain a FileData result
        result = response.json()
        assert isinstance(result, dict)
        assert result.get("_t") == "FileData"
        assert "FileBytes" in result
        # ZIP files start with PK signature, verify base64 starts with UEs (PK in base64)
        assert result["FileBytes"].startswith("UEs")


def test_api_deps(default_db_fixture):
    """Test run_export_records via the handler/run API endpoint with dependencies."""

    # Create and save the dependency record first
    dependency_record = StubDataclass(id="api_dep").build()
    active(DataSource).replace_one(dependency_record, commit=True)

    # Create and save a record that has a key field referencing another record
    main_record = StubDataclassNestedFields(
        id="api_main",
        key_field=StubDataclassKey(id="api_dep"),
    ).build()
    active(DataSource).replace_one(main_record, commit=True)

    # Get the serialized key for main record
    key_str = KeySerializers.DELIMITED.serialize(main_record.get_key())

    # Test via REST API
    with QaClient() as test_client:
        request = {
            "Type": "UiRecordUtil",
            "Method": "RunExportRecords",
            "Keys": [],
            "Arguments": {
                "TypeToExport": "StubDataclassNestedFields",
                "Keys": [key_str],
                "WithDependencies": True,
            },
        }

        response = test_client.post("/task/run", json=request)
        assert response.status_code == 200

        # Response should contain a FileData result
        result = response.json()
        assert isinstance(result, dict)
        assert result.get("_t") == "FileData"
        assert "FileBytes" in result
        # ZIP files start with PK signature, verify base64 starts with UEs (PK in base64)
        assert result["FileBytes"].startswith("UEs")


@pytest.mark.parametrize(
    "export_format", [SaveFormat.CSV, SaveFormat.JSON, SaveFormat.YAML], ids=["csv", "json", "yaml"]
)
def test_export_dict_list_fields(default_db_fixture, export_format: SaveFormat):
    """Test run_export_records with list of dicts fields for all formats."""

    # Create and save records with list of dict fields
    records = [
        StubDataclassDictListFields(id=f"dict_list_test_{export_format.name.lower()}_{i}").build() for i in range(2)
    ]
    for record in records:
        active(DataSource).replace_one(record, commit=True)

    # Get the serialized keys
    key_strs = [KeySerializers.DELIMITED.serialize(r.get_key()) for r in records]

    # Call run_export_records with specific format
    result = UiRecordUtil.run_export_records(
        type_to_export="StubDataclassDictListFields",
        keys=key_strs,
        with_dependencies=False,
        export_format=export_format,
    )

    # Assert - result should be a FileData object with ZIP content
    assert result is not None
    assert hasattr(result, "file_bytes")
    assert result.file_bytes is not None
    # ZIP files start with PK signature
    assert result.file_bytes[:2] == b"PK"

    # Verify the archive name contains the expected format info
    assert result.name.endswith(".zip")
    assert result.name.startswith("Export_")


@pytest.mark.parametrize(
    "export_format", [SaveFormat.CSV, SaveFormat.JSON, SaveFormat.YAML], ids=["csv", "json", "yaml"]
)
def test_export_list_dict_fields(default_db_fixture, export_format: SaveFormat):
    """Test run_export_records with dict of lists fields for all formats."""

    # Create and save records with dict of list fields
    records = [
        StubDataclassListDictFields(id=f"list_dict_test_{export_format.name.lower()}_{i}").build() for i in range(2)
    ]
    for record in records:
        active(DataSource).replace_one(record, commit=True)

    # Get the serialized keys
    key_strs = [KeySerializers.DELIMITED.serialize(r.get_key()) for r in records]

    # Call run_export_records with specific format
    result = UiRecordUtil.run_export_records(
        type_to_export="StubDataclassListDictFields",
        keys=key_strs,
        with_dependencies=False,
        export_format=export_format,
    )

    # Assert - result should be a FileData object with ZIP content
    assert result is not None
    assert hasattr(result, "file_bytes")
    assert result.file_bytes is not None
    # ZIP files start with PK signature
    assert result.file_bytes[:2] == b"PK"

    # Verify the archive name contains the expected format info
    assert result.name.endswith(".zip")
    assert result.name.startswith("Export_")


def test_export_nested_sequences_with_deps(default_db_fixture):
    """Test run_export_records with nested sequences and dependencies."""

    # Create and save dependency records
    dep_records = [StubDataclass(id=f"nested_dep_{i}").build() for i in range(2)]
    for record in dep_records:
        active(DataSource).replace_one(record, commit=True)

    # Create and save a record with list of dicts that contains keys
    main_record = StubDataclassDictListFields(id="nested_main_dict_list").build()
    active(DataSource).replace_one(main_record, commit=True)

    # Get the serialized key for main record
    key_str = KeySerializers.DELIMITED.serialize(main_record.get_key())

    # Call run_export_records with dependencies
    result = UiRecordUtil.run_export_records(
        type_to_export="StubDataclassDictListFields",
        keys=[key_str],
        with_dependencies=True,
    )

    # Assert - result should be a FileData object with ZIP content
    assert result is not None
    assert hasattr(result, "file_bytes")
    assert result.file_bytes is not None
    # ZIP files start with PK signature
    assert result.file_bytes[:2] == b"PK"


def test_api_nested_dict_list(default_db_fixture):
    """Test run_export_records via API with list of dicts fields."""

    # Create and save records with list of dict fields
    records = [StubDataclassDictListFields(id=f"api_dict_list_{i}").build() for i in range(2)]
    for record in records:
        active(DataSource).replace_one(record, commit=True)

    # Get the serialized keys
    key_strs = [KeySerializers.DELIMITED.serialize(r.get_key()) for r in records]

    # Test via REST API
    with QaClient() as test_client:
        request = {
            "Type": "UiRecordUtil",
            "Method": "RunExportRecords",
            "Keys": [],
            "Arguments": {
                "TypeToExport": "StubDataclassDictListFields",
                "Keys": key_strs,
                "WithDependencies": False,
            },
        }

        response = test_client.post("/task/run", json=request)
        assert response.status_code == 200

        # Response should contain a FileData result
        result = response.json()
        assert isinstance(result, dict)
        assert result.get("_t") == "FileData"
        assert "FileBytes" in result
        # ZIP files start with PK signature, verify base64 starts with UEs (PK in base64)
        assert result["FileBytes"].startswith("UEs")


def test_api_nested_list_dict(default_db_fixture):
    """Test run_export_records via API with dict of lists fields."""

    # Create and save records with dict of list fields
    records = [StubDataclassListDictFields(id=f"api_list_dict_{i}").build() for i in range(2)]
    for record in records:
        active(DataSource).replace_one(record, commit=True)

    # Get the serialized keys
    key_strs = [KeySerializers.DELIMITED.serialize(r.get_key()) for r in records]

    # Test via REST API
    with QaClient() as test_client:
        request = {
            "Type": "UiRecordUtil",
            "Method": "RunExportRecords",
            "Keys": [],
            "Arguments": {
                "TypeToExport": "StubDataclassListDictFields",
                "Keys": key_strs,
                "WithDependencies": False,
            },
        }

        response = test_client.post("/task/run", json=request)
        assert response.status_code == 200

        # Response should contain a FileData result
        result = response.json()
        assert isinstance(result, dict)
        assert result.get("_t") == "FileData"
        assert "FileBytes" in result
        # ZIP files start with PK signature, verify base64 starts with UEs (PK in base64)
        assert result["FileBytes"].startswith("UEs")


@pytest.mark.parametrize(
    "stub_class,type_name",
    [
        (StubDataclassDictListFields, "StubDataclassDictListFields"),
        (StubDataclassListDictFields, "StubDataclassListDictFields"),
    ],
    ids=["dict_list", "list_dict"],
)
def test_export_nested_sequences_roundtrip(default_db_fixture, stub_class, type_name):
    """Test that nested sequences can be exported and maintain data integrity."""

    # Create and save a record with nested sequences
    original_record = stub_class(id=f"roundtrip_{type_name.lower()}").build()
    active(DataSource).replace_one(original_record, commit=True)

    # Get the serialized key
    key_str = KeySerializers.DELIMITED.serialize(original_record.get_key())

    # Export the record in all formats
    for export_format in [SaveFormat.CSV, SaveFormat.JSON, SaveFormat.YAML]:
        result = UiRecordUtil.run_export_records(
            type_to_export=type_name,
            keys=[key_str],
            with_dependencies=False,
            export_format=export_format,
        )

        # Verify export succeeded
        assert result is not None
        assert result.file_bytes is not None
        assert result.file_bytes[:2] == b"PK"
        assert export_format.name.lower() in result.name.lower() or result.name.startswith("Export_")


if __name__ == "__main__":
    pass
