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

from abc import ABC
from abc import abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence
from frozendict import frozendict
from cl.runtime.file.file_util import FileUtil
from cl.runtime.file.reader_key import ReaderKey
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.record_mixin import RecordMixin


@dataclass(slots=True, kw_only=True)
class Reader(ReaderKey, RecordMixin, ABC):
    """Read records from the specified storage and save them to the active data source."""

    def get_key(self) -> ReaderKey:
        return ReaderKey(reader_id=self.reader_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        # Use globally unique UUIDv7-based timestamp if not specified
        if self.reader_id is None:
            self.reader_id = Timestamp.create()

    @abstractmethod
    def load_file(self, *, file_path: str) -> frozendict[str, tuple[RecordMixin, ...]]:
        """
        Load one or multiple records from a single file grouped by dataset.

        Args:
            file_path: Absolute path to the file to load
        Returns:
            Frozendict mapping dataset identifier to a tuple of records.
            Records without an explicit dataset are placed under the root dataset "/".
        Raises:
            RuntimeError: If an error occurs during file reading or record loading
        """

    def load_all(
        self,
        *,
        dirs: Sequence[str],
        ext: str,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> frozendict[str, tuple[RecordMixin, ...]]:
        """
        Load records from files in the specified dirs with the specified extension.

        Args:
            dirs: Directories where file search is performed
            ext: File extension to search for without the leading dot (e.g., "json" or "csv")
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        Returns:
            Frozendict mapping dataset identifier to a tuple of records.
            Records without an explicit dataset are placed under the root dataset "/".
        Raises:
            RuntimeError: If an error occurs during file reading or record loading
        """

        file_paths = FileUtil.enumerate_files(
            dirs=dirs,
            ext=ext,
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        merged: dict[str, list[RecordMixin]] = defaultdict(list)
        for file_path in file_paths:
            file_result = self.load_file(file_path=file_path)
            for dataset, records in file_result.items():
                merged[dataset].extend(records)
        return frozendict({k: tuple(v) for k, v in merged.items()})
