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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey


def test_insert_stores_in_specified_dataset(multi_db_fixture):
    """Insert stores a record in the specified dataset."""
    ds = active(DataSource)

    ds.insert_one(StubDataclass(id="r1").build(), dataset="/A", commit=True)

    # Record is found when loading from its dataset
    loaded = ds.load_all(StubDataclassKey, datasets=["/A"])
    assert len(loaded) == 1
    assert loaded[0].id == "r1"

    # Record is found when loading without dataset filter (all datasets)
    loaded = ds.load_all(StubDataclassKey)
    assert any(r.id == "r1" for r in loaded)

    # Record is NOT found in a different dataset
    loaded = ds.load_all(StubDataclassKey, datasets=["/B"])
    assert not any(r.id == "r1" for r in loaded)


def test_insert_default_dataset_is_root(multi_db_fixture):
    """Insert without explicit dataset stores in root '/'."""
    ds = active(DataSource)

    ds.insert_one(StubDataclass(id="r1").build(), commit=True)

    # Record is found in root dataset
    loaded = ds.load_all(StubDataclassKey, datasets=["/"])
    assert len(loaded) == 1
    assert loaded[0].id == "r1"


def test_insert_duplicate_key_same_dataset_fails(multi_db_fixture):
    """Insert with the same key and same dataset fails."""
    ds = active(DataSource)

    ds.insert_one(StubDataclass(id="r1").build(), dataset="/A", commit=True)

    with pytest.raises(Exception):
        ds.insert_one(StubDataclass(id="r1").build(), dataset="/A", commit=True)


def test_insert_duplicate_key_different_dataset_fails(multi_db_fixture):
    """Insert with the same key in a different dataset fails because a key can only be in one dataset."""
    ds = active(DataSource)

    ds.insert_one(StubDataclass(id="r1").build(), dataset="/A", commit=True)

    with pytest.raises(Exception):
        ds.insert_one(StubDataclass(id="r1").build(), dataset="/B", commit=True)


def test_replace_same_dataset(multi_db_fixture):
    """Replace updates a record within the same dataset."""
    ds = active(DataSource)

    ds.insert_one(StubDataclassDerived(id="r1", derived_str_field="v1").build(), dataset="/A", commit=True)
    ds.replace_one(StubDataclassDerived(id="r1", derived_str_field="v2").build(), dataset="/A", commit=True)

    loaded = ds.load_all(StubDataclassKey, datasets=["/A"])
    assert len(loaded) == 1
    assert loaded[0].id == "r1"
    assert loaded[0].derived_str_field == "v2"


def test_replace_moves_record_to_new_dataset(multi_db_fixture):
    """Replace with a different dataset moves the record from the old dataset to the new one."""
    ds = active(DataSource)

    ds.insert_one(StubDataclassDerived(id="r1", derived_str_field="v1").build(), dataset="/A", commit=True)

    # Replace to a different dataset
    ds.replace_one(StubDataclassDerived(id="r1", derived_str_field="v2").build(), dataset="/B", commit=True)

    # Record is no longer in dataset /A
    loaded_a = ds.load_all(StubDataclassKey, datasets=["/A"])
    assert not any(r.id == "r1" for r in loaded_a)

    # Record is now in dataset /B with updated data
    loaded_b = ds.load_all(StubDataclassKey, datasets=["/B"])
    assert len(loaded_b) == 1
    assert loaded_b[0].id == "r1"
    assert loaded_b[0].derived_str_field == "v2"

    # Only one copy exists across all datasets
    loaded_all = ds.load_all(StubDataclassKey)
    r1_records = [r for r in loaded_all if r.id == "r1"]
    assert len(r1_records) == 1


def test_load_all_datasets_returns_all(multi_db_fixture):
    """Load without dataset filter returns records from all datasets."""
    ds = active(DataSource)

    ds.insert_one(StubDataclass(id="r1").build(), dataset="/A", commit=True)
    ds.insert_one(StubDataclass(id="r2").build(), dataset="/B", commit=True)
    ds.insert_one(StubDataclass(id="r3").build(), dataset="/", commit=True)

    loaded = ds.load_all(StubDataclassKey)
    loaded_ids = {r.id for r in loaded}
    assert loaded_ids >= {"r1", "r2", "r3"}


def test_load_specific_dataset_filters(multi_db_fixture):
    """Load with dataset filter returns only records from those datasets."""
    ds = active(DataSource)

    ds.insert_one(StubDataclass(id="r1").build(), dataset="/A", commit=True)
    ds.insert_one(StubDataclass(id="r2").build(), dataset="/B", commit=True)
    ds.insert_one(StubDataclass(id="r3").build(), dataset="/", commit=True)

    # Single dataset filter
    loaded_a = ds.load_all(StubDataclassKey, datasets=["/A"])
    assert {r.id for r in loaded_a} == {"r1"}

    loaded_b = ds.load_all(StubDataclassKey, datasets=["/B"])
    assert {r.id for r in loaded_b} == {"r2"}

    # Multiple datasets filter
    loaded_ab = ds.load_all(StubDataclassKey, datasets=["/A", "/B"])
    assert {r.id for r in loaded_ab} == {"r1", "r2"}


if __name__ == "__main__":
    pytest.main([__file__])
