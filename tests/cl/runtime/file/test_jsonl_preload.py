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
from cl.runtime.file.jsonl_reader import JsonlReader
from cl.runtime.settings.preload_settings import PreloadSettings
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass


def test_jsonl_preload(default_db_fixture):
    """Test that JSONL preload files from preload directories are loaded correctly.

    Verifies that both single-record (StubDataclass.One.jsonl) and multi-record
    (StubDataclass.Many.jsonl) preload files are discovered and deserialized.
    """

    # Get preload directories
    preload_settings = PreloadSettings.instance()
    dirs = preload_settings.preload_dirs

    # Load all JSONL files from preload directories
    jsonl_reader = JsonlReader().build()
    records = list(jsonl_reader.load_all(dirs=dirs, ext="jsonl").get("\\", ()))

    # Check that StubDataclass.One.jsonl was loaded
    matching = [r for r in records if isinstance(r, StubDataclass) and r.id == "jsonl_one"]
    assert len(matching) == 1, f"Expected to find jsonl_one in loaded records, got {len(matching)}"

    # Check that both records from StubDataclass.Many.jsonl were loaded
    matching = [r for r in records if isinstance(r, StubDataclass) and r.id in ("jsonl_many_1", "jsonl_many_2")]
    assert len(matching) == 2, (
        f"Expected 2 records from JSONL (jsonl_many_1, jsonl_many_2), got {len(matching)}. "
        f"Found ids: {[r.id for r in matching]}"
    )


if __name__ == "__main__":
    pytest.main([__file__])
