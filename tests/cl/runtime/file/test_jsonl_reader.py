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
import time
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


def test_performance(default_db_fixture, tmp_path):
    """Time load_all for generated JSONL files of 100, 1000, and 10000 rows."""

    row_counts = [100, 1000, 10000]
    results = []

    for row_count in row_counts:
        # Generate JSONL file
        lines = []
        for i in range(1, row_count + 1):
            lines.append(f'{{"derived_str_field":"test_derived_str_field_value_{i}","id":"derived_id_{i}"}}')
        jsonl_path = os.path.join(str(tmp_path), "StubDataclassDerived.jsonl")
        with open(jsonl_path, "wb") as f:
            f.write("\n".join(lines).encode() + b"\n")

        jsonl_reader = JsonlReader().build()
        start = time.perf_counter()
        records = jsonl_reader.load_all(dirs=[str(tmp_path)], ext="jsonl")
        elapsed = time.perf_counter() - start

        assert len(records) == row_count
        results.append((row_count, elapsed))

        # Clean up generated file before next iteration
        os.remove(jsonl_path)

    # Write bench CSV next to this test file
    bench_path = os.path.join(os.path.dirname(__file__), "test_jsonl_reader.bench.csv")
    with open(bench_path, "w", newline="", encoding="utf-8") as f:
        f.write("Rows,TimeSec\n")
        for row_count, elapsed in results:
            f.write(f"{row_count},{elapsed:.6f}\n")


if __name__ == "__main__":
    pytest.main([__file__])
