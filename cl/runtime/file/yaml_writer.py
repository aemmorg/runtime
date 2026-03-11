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
from dataclasses import dataclass
from typing import Iterable
from typing import Sequence
from cl.runtime.file.file_data import FileData
from cl.runtime.file.file_kind import FileKind
from cl.runtime.file.file_util import FileUtil
from cl.runtime.file.writer import Writer
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.yaml_encoders import YamlEncoders

# Serializer for YAML format (same as JSON)
_SERIALIZER = DataSerializers.FOR_JSON

# Encoder for YAML file
_ENCODER = YamlEncoders.DEFAULT


@dataclass(slots=True, kw_only=True)
class YamlWriter(Writer):
    """Class to save records to YAML files."""

    def to_files(
        self,
        records: Sequence[RecordMixin],
    ) -> Iterable[FileData]:
        """
        Save records as YAML files.
        Each record is saved in its own file with name matching its key.
        Files are grouped in folders by base type.

        Args:
            records: Sequence of records to save

        Returns:
            Iterable of FileData objects containing YAML files as embedded binary content
        """
        if records is None:
            return

        for record in records:
            if record is None:
                continue

            # Serialize record to JSON dict and then to YAML string with OS-specific line endings
            record_dict = _SERIALIZER.serialize(record)
            record_yaml_str = _ENCODER.encode(record_dict).replace("\n", os.linesep)

            # Build file path from record type and key
            dirname_for_record = FileUtil.get_dirname_for_record(record)
            filename_for_record = FileUtil.get_filename_for_record(record, ext="yaml")

            yield FileData(
                name=filename_for_record,
                file_kind=FileKind.YAML,
                relative_path=dirname_for_record,
                file_bytes=record_yaml_str.encode("utf-8"),
            ).build()
