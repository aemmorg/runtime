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
from typing import Iterable
from typing import Sequence
from openpyxl import Workbook
from cl.runtime.file.csv_writer import CsvWriter
from cl.runtime.file.file_data import FileData
from cl.runtime.file.file_kind import FileKind
from cl.runtime.file.writer import Writer
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename


class ExcelWriter(Writer):
    """Class to save records to Excel files without formatting."""

    def to_files(self, records: Sequence[RecordMixin]) -> Iterable[FileData]:
        """
        Save records as Excel files.
        Records are grouped into one file by record type.

        Args:
            records: Sequence of records to save

        Returns:
            Iterable of FileData objects containing Excel files as embedded binary content
        """

        records_by_type = CsvWriter._group_records_by_type(records)

        for record_type, records_group in records_by_type.items():
            if records_group is None:
                continue

            records_df = CsvWriter._serialize_records_into_df(records_group, columns=None)

            if records_df.empty:
                continue

            wb = Workbook()
            ws = wb.active
            ws.title = "Sheet1"

            headers = list(records_df.columns)
            ws.append(headers)

            for _, row in records_df.iterrows():
                ws.append([row[col] for col in headers])

            buf = io.BytesIO()
            wb.save(buf)

            file_name = f"{typename(record_type)}.xlsx"
            yield FileData(name=file_name, file_bytes=buf.getvalue(), file_kind=FileKind.XLSX).build()
