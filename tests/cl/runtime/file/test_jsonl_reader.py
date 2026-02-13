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
from cl.runtime.file.jsonl_reader import JsonlReader
from cl.runtime.qa.qa_util import QaUtil
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey


def test_load_all(default_db_fixture):
    """Test JsonlReader.load_all() with StubDataclassDerived records."""

    env_dir = QaUtil.get_test_dir_from_call_stack()

    jsonl_reader = JsonlReader().build()
    records = jsonl_reader.load_all(dirs=[env_dir], ext="jsonl", file_include_patterns=["StubDataclassDerived.*"])
    active(DataSource).insert_many(records, commit=True)

    # Verify
    for i in range(1, 3):
        expected_record = StubDataclassDerived(
            id=f"derived_id_{i}", derived_str_field=f"test_derived_str_field_value_{i}"
        ).build()
        key = StubDataclassKey(id=f"derived_id_{i}").build()
        record = active(DataSource).load_one(key)
        assert record == expected_record


def test_check_or_fix_format(work_dir_fixture):
    """Test JsonlReader.check_or_fix_file() with valid and invalid JSONL format samples.

    Fixture files:
    - valid_jsonl_format.jsonl: canonical compact JSON -> passes validation
    - invalid_jsonl_format.jsonl: extra whitespace/non-canonical formatting -> fails validation
    """

    # Valid file passes check
    assert JsonlReader.check_or_fix_file("valid_jsonl_format.jsonl", fix=False)

    # Invalid file has non-canonical formatting
    assert not JsonlReader.check_or_fix_file("invalid_jsonl_format.jsonl", fix=False)


if __name__ == "__main__":
    pytest.main([__file__])
