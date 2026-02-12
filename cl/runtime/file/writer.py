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

import io
import os
import zipfile
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Iterable
from typing import Sequence
from cl.runtime.file.file_data import FileData
from cl.runtime.file.file_kind import FileKind
from cl.runtime.file.file_util import FileUtil
from cl.runtime.file.writer_key import WriterKey
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.none_checks import NoneChecks
from cl.runtime.records.record_mixin import RecordMixin


@dataclass(slots=True, kw_only=True)
class Writer(WriterKey, RecordMixin, ABC):
    """Read records from the specified storage and save them to the active data source."""

    def get_key(self) -> WriterKey:
        return WriterKey(writer_id=self.writer_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        # Use globally unique UUIDv7-based timestamp if not specified
        if self.writer_id is None:
            self.writer_id = Timestamp.create()

    @abstractmethod
    def to_files(
        self,
        records: Sequence[RecordMixin],
    ) -> Iterable[FileData]:
        """
        Create FileData objects of serialized records in binary format.

        Args:
            records: Records to serialize
        Returns:
            FileData objects containing serialized records in binary format
        """
        pass

    def to_zip(
        self,
        records: Sequence[RecordMixin],
    ) -> FileData:
        """
        Create a FileData object containing a ZIP archive of serialized records in binary format.

        Args:
            records: Sequence of records to archive

        Returns:
            FileData object with the ZIP archive as embedded binary content

        Raises:
            RuntimeError: If records parameter is None or empty
        """

        NoneChecks.guard_not_none(records)

        # Save all records in bytes format first
        # Specific format is handled in save_all implementation
        files = self.to_files(records)

        # Create in-memory buffer for the ZIP archive
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                if file.relative_path:
                    file_path = os.path.join(file.relative_path, file.name)
                else:
                    file_path = file.name

                # Write binary content to the ZIP archive
                zip_file.writestr(file_path, file.file_bytes)

        # Get the ZIP bytes
        zip_buffer.seek(0)
        zip_bytes = zip_buffer.getvalue()

        # Create and return FileData object
        archive_name = FileUtil.get_archive_name_for_records(records)
        return FileData(
            name=archive_name,
            file_kind=FileKind.ZIP,
            file_bytes=zip_bytes,
        ).build()
