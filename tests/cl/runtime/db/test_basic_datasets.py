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

from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.data_source_util import DataSourceUtil
from cl.runtime.records.record_type_presence import RecordTypePresence
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_info import TypeInfo
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey


def test_single_dataset(multi_db_fixture):
    """Test that a single dataset does not trigger has_multiple_datasets."""
    ds = active(DataSource)

    records = [
        StubDataclass(id="r1").build(),
        StubDataclass(id="r2").build(),
    ]
    ds.insert_many(records, dataset="/", commit=True)

    # All records are in root dataset
    loaded = ds.load_all(StubDataclassKey)
    assert len(loaded) == 2

    # has_multiple_datasets should be False
    assert DataSourceUtil.has_multiple_datasets(ds, record_type=StubDataclass) is False


def test_two_datasets_root_and_child(multi_db_fixture):
    """Test records in root and one child dataset."""
    ds = active(DataSource)

    rec_root = StubDataclass(id="root").build()
    rec_a = StubDataclass(id="a").build()

    ds.insert_one(rec_root, dataset="/", commit=True)
    ds.insert_one(rec_a, dataset="/A", commit=True)

    # Load all without dataset filter
    all_records = ds.load_all(StubDataclassKey)
    assert len(all_records) == 2

    # Load with specific dataset filter
    root_only = ds.load_all(StubDataclassKey, datasets=["/"])
    assert len(root_only) == 1
    assert root_only[0].id == "root"

    a_only = ds.load_all(StubDataclassKey, datasets=["/A"])
    assert len(a_only) == 1
    assert a_only[0].id == "a"

    # has_multiple_datasets should be True
    assert DataSourceUtil.has_multiple_datasets(ds, record_type=StubDataclass) is True


def test_multiple_datasets(multi_db_fixture):
    """Test records spread across /, /A, /B, /A/B datasets."""
    ds = active(DataSource)

    rec_root = StubDataclass(id="root").build()
    rec_a = StubDataclass(id="a").build()
    rec_b = StubDataclass(id="b").build()
    rec_ab = StubDataclass(id="ab").build()

    ds.insert_one(rec_root, dataset="/", commit=True)
    ds.insert_one(rec_a, dataset="/A", commit=True)
    ds.insert_one(rec_b, dataset="/B", commit=True)
    ds.insert_one(rec_ab, dataset="/A/B", commit=True)

    # Load all without dataset filter
    all_records = ds.load_all(StubDataclassKey)
    assert len(all_records) == 4

    # Load with specific dataset filter
    root_only = ds.load_all(StubDataclassKey, datasets=["/"])
    assert len(root_only) == 1
    assert root_only[0].id == "root"

    a_only = ds.load_all(StubDataclassKey, datasets=["/A"])
    assert len(a_only) == 1
    assert a_only[0].id == "a"

    b_only = ds.load_all(StubDataclassKey, datasets=["/B"])
    assert len(b_only) == 1
    assert b_only[0].id == "b"

    ab_only = ds.load_all(StubDataclassKey, datasets=["/A/B"])
    assert len(ab_only) == 1
    assert ab_only[0].id == "ab"

    # Load with multiple dataset filter
    a_and_b = ds.load_all(StubDataclassKey, datasets=["/A", "/B"])
    assert len(a_and_b) == 2
    loaded_ids = {r.id for r in a_and_b}
    assert loaded_ids == {"a", "b"}


def test_multiple_datasets_presence(multi_db_fixture):
    """Test that RecordTypePresence correctly tracks per-dataset presence."""
    ds = active(DataSource)

    ds.insert_one(StubDataclass(id="root").build(), dataset="/", commit=True)
    ds.insert_one(StubDataclass(id="a").build(), dataset="/A", commit=True)
    ds.insert_one(StubDataclass(id="b").build(), dataset="/B", commit=True)
    ds.insert_one(StubDataclass(id="ab").build(), dataset="/A/B", commit=True)

    # Check RecordTypePresence records
    presences = ds.load_by_type(RecordTypePresence)

    # Filter presences for StubDataclass using TypeInfo
    matching_type_names = set(TypeInfo.get_child_and_self_type_names(StubDataclass))
    stub_datasets = {p.dataset for p in presences if typename(p.record_type) in matching_type_names}
    assert stub_datasets == {"/", "/A", "/B", "/A/B"}


def test_multiple_datasets_derived_types(multi_db_fixture):
    """Test dataset presence tracking with derived types."""
    ds = active(DataSource)

    # Insert base type in root, derived type in /A
    ds.insert_one(StubDataclass(id="base").build(), dataset="/", commit=True)
    ds.insert_one(StubDataclassDerived(id="derived").build(), dataset="/A", commit=True)

    # Load all from the table (key type)
    all_records = ds.load_all(StubDataclassKey)
    assert len(all_records) == 2

    # has_multiple_datasets for the base type should be True (records in / and /A)
    assert DataSourceUtil.has_multiple_datasets(ds, record_type=StubDataclass) is True

    # has_multiple_datasets for derived type should be False (only in /A)
    assert DataSourceUtil.has_multiple_datasets(ds, record_type=StubDataclassDerived) is False


def test_insert_many_with_dataset(multi_db_fixture):
    """Test insert_many with explicit dataset parameter."""
    ds = active(DataSource)

    records_a = [StubDataclass(id="a1").build(), StubDataclass(id="a2").build()]
    records_b = [StubDataclass(id="b1").build()]

    ds.insert_many(records_a, dataset="/A", commit=True)
    ds.insert_many(records_b, dataset="/B", commit=True)

    # Load all
    all_records = ds.load_all(StubDataclassKey)
    assert len(all_records) == 3

    # Load per dataset
    a_records = ds.load_all(StubDataclassKey, datasets=["/A"])
    assert len(a_records) == 2

    b_records = ds.load_all(StubDataclassKey, datasets=["/B"])
    assert len(b_records) == 1


def test_empty_dataset_filter(multi_db_fixture):
    """Test loading from a dataset that has no records."""
    ds = active(DataSource)

    ds.insert_one(StubDataclass(id="root").build(), dataset="/", commit=True)

    # Load from a dataset that has no records
    empty = ds.load_all(StubDataclassKey, datasets=["/NonExistent"])
    assert len(empty) == 0
