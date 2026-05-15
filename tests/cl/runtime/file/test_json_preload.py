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
from cl.runtime.configurations.preload_configuration import PreloadConfiguration
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey


def test_json_preload(default_db_fixture, work_dir_fixture):
    """Test that JSON preload files are loaded correctly.

    Verifies that both single-record (StubDataclass.One.json) and multi-record
    (StubDataclass.Many.json) preload files are discovered and loaded into the DB.
    """

    # Preload JSON files from the test work directory into the DB
    PreloadConfiguration(dirs=[work_dir_fixture]).build().run_configure()

    # Verify the records are present in DB
    records = active(DataSource).load_by_type(StubDataclassKey, cast_to=StubDataclass)

    # Check that StubDataclass.One.json was loaded
    matching = [r for r in records if r.id == "json_one"]
    assert len(matching) == 1, f"Expected to find json_one in loaded records, got {len(matching)}"

    # Check that both records from StubDataclass.Many.json were loaded
    matching = [r for r in records if r.id in ("json_many_1", "json_many_2")]
    assert len(matching) == 2, (
        f"Expected 2 records from JSON (json_many_1, json_many_2), got {len(matching)}. "
        f"Found ids: {[r.id for r in matching]}"
    )


if __name__ == "__main__":
    pytest.main([__file__])
