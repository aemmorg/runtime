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
from typing import Iterable
from typing import Sequence
import pandas as pd
from cl.runtime.file.file_data import FileData
from cl.runtime.file.file_kind import FileKind
from cl.runtime.file.writer import Writer
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers

_KEY_SERIALIZER = KeySerializers.DELIMITED
_CSV_SERIALIZER = DataSerializers.FOR_CSV


class CsvWriter(Writer):
    def to_files(self, records: Sequence[RecordMixin]) -> Iterable[FileData]:
        """
        Save records as CSV files.
        Records are grouped into one file by record type.

        Args:
            records: Sequence of records to save

        Returns:
            Iterable of FileData objects containing CSV files as embedded binary content
        """

        records_by_type = self._group_records_by_type(records)

        for record_type, records_group in records_by_type.items():
            if records_group is None:
                continue

            # Serialize records of the same type to a single DataFrame
            records_df = self._serialize_records_into_df(records_group, columns=None)

            if records_df.empty:
                continue

            # Convert DataFrame to CSV string with OS-specific line endings
            csv_string = records_df.to_csv(index=False, encoding="utf-8", lineterminator=os.linesep)

            # Convert CSV string to bytes and yield FileData
            file_name = f"{record_type.__name__}.csv"
            yield FileData(name=file_name, file_bytes=csv_string.encode("utf-8"), file_kind=FileKind.CSV).build()

    @classmethod
    def _serialize_records_into_df(
        cls,
        records: Sequence[RecordMixin],
        columns: Sequence[str] | None = None,
    ) -> pd.DataFrame:
        """
        Convert records to pd.DataFrame format for CSV.
        Records must be the same type.

        Args:
            records: Records to serialize.
            columns: Columns to include in the DataFrame. If None, include all columns.

        Returns:
            pandas DataFrame containing serialized records
        """
        if records is None:
            return pd.DataFrame()

        # Serialize records with CSV serializer
        record_dicts = []
        for record in records:
            if record is None:
                continue

            serialized_record = _CSV_SERIALIZER.serialize(record)
            serialized_record.pop("_type", None)
            # Convert snake_case field names to PascalCase column headers
            serialized_record = {
                CaseUtil.snake_to_pascal_case_keep_trailing_underscore(k): v for k, v in serialized_record.items()
            }
            record_dicts.append(serialized_record)

        # Use pandas df to transform list of dicts to table format
        df = pd.DataFrame(record_dicts, columns=columns)
        return df

    @classmethod
    def _group_records_by_type(cls, records: Sequence[RecordMixin]) -> dict[type, list[RecordMixin]]:
        """
        Group records by their type.

        Args:
            records: Sequence of records to group by type

        Returns:
            Dictionary mapping record types to lists of records
        """
        if records is None:
            return {}

        type_to_records = defaultdict(list)
        for record in records:
            if record is not None:
                type_to_records[type(record)].append(record)

        return dict(type_to_records)
