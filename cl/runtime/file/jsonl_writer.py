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

import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable
from typing import Sequence
import orjson
from cl.runtime.file.file_data import FileData
from cl.runtime.file.file_kind import FileKind
from cl.runtime.file.writer import Writer
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.serializers.data_serializers import DataSerializers

_SERIALIZER = DataSerializers.FOR_JSON


@dataclass(slots=True, kw_only=True)
class JsonlWriter(Writer):
    """Save records to JSONL (JSON Lines) files, one compact JSON object per line.

    Unlike JsonWriter which creates one file per record, JsonlWriter groups all records
    of the same type into a single file (similar to CsvWriter). Uses orjson for compact
    serialization without pretty-printing.
    """

    def to_files(
        self,
        records: Sequence[RecordMixin],
    ) -> Iterable[FileData]:
        """
        Save records as JSONL files.
        Records are grouped into one file per record type, one compact JSON object per line.

        Args:
            records: Sequence of records to save

        Returns:
            Iterable of FileData objects containing JSONL files as embedded binary content
        """
        if records is None:
            return

        # Group records by type
        records_by_type: dict[type, list[RecordMixin]] = defaultdict(list)
        for record in records:
            if record is not None:
                records_by_type[type(record)].append(record)

        for record_type, records_group in records_by_type.items():
            # Serialize each record to a compact JSON line using orjson (no pretty-printing)
            lines = []
            for record in records_group:
                record_dict = _SERIALIZER.serialize(record)
                lines.append(orjson.dumps(record_dict))

            # Join lines with OS-specific line endings and add trailing newline per JSONL convention
            eol = os.linesep.encode()
            jsonl_bytes = eol.join(lines) + eol

            # One file per type, named after the record class
            file_name = f"{typename(record_type)}.jsonl"
            yield FileData(
                name=file_name,
                file_kind=FileKind.JSONL,
                file_bytes=jsonl_bytes,
            ).build()
