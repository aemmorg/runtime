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

import csv
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from typing import Sequence
from frozendict import frozendict
from cl.runtime.file.file_util import FileUtil
from cl.runtime.file.reader import Reader
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.char_util import CharUtil
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.serializers.csv_util import CsvUtil
from cl.runtime.serializers.data_serializers import DataSerializers

_SERIALIZER = DataSerializers.FOR_CSV


@dataclass(slots=True, kw_only=True)
class CsvReader(Reader):
    """Helper class for working with CSV files."""

    generated: bool | None = None
    """Set to True for generated CSV files with sep= sentinel prefix."""

    def load_file(self, *, file_path: str) -> frozendict[str, tuple[RecordMixin, ...]]:
        """Load records from a single CSV file grouped by dataset."""

        generated = self.generated
        if generated is None and file_path.endswith(".generated.csv"):
            generated = True

        with open(file_path, mode="r", encoding="utf-8") as f:
            has_sentinel = f.readline().rstrip("\r\n").startswith("sep=")

        if generated is None and has_sentinel:
            xlsx_file_path = self._xlsx_path_from_csv(file_path)
            raise RuntimeError(
                f"CSV file {file_path} has sep= prefix, indicating it has been "
                f"generated from {xlsx_file_path}. Read the .xlsx file instead."
            )
        if generated and not has_sentinel:
            xlsx_file_path = self._xlsx_path_from_csv(file_path)
            raise RuntimeError(
                f"CSV file {file_path} has no sep= prefix, indicating it has been "
                f"edited manually after it has been generated from {xlsx_file_path}. "
                f"Move changes to the .xlsx file and delete {file_path} to continue."
            )

        records_by_dataset: dict[str, list[RecordMixin]] = defaultdict(list)
        try:
            record_type = FileUtil.get_type_from_filename(file_path)

            with open(file_path, mode="r", encoding="utf-8") as file:
                if has_sentinel:
                    file.readline()

                csv_reader = csv.DictReader(file)
                row_dicts = [row_dict for row_dict in csv_reader]

                invalid_rows = {
                    index
                    for index, row_dict in enumerate(row_dicts)
                    for key in row_dict.keys()
                    if key is None or key == ""  # TODO: Add other checks for invalid keys
                }

                if invalid_rows:
                    rows_str = "".join([f"Row: {invalid_row}\n" for invalid_row in invalid_rows])
                    raise RuntimeError(
                        "Misaligned values found in the following rows.\n"
                        "Check the placement of commas and double quotes.\n" + rows_str
                    )

                for row_dict in row_dicts:
                    record, dataset = self._deserialize_row(record_type=record_type, row_dict=row_dict)
                    records_by_dataset[dataset or "/"].append(record)
        except Exception as e:
            raise RuntimeError(f"Failed to load CSV file {file_path}. Error: {e}") from e

        return frozendict({k: tuple(v) for k, v in records_by_dataset.items()})

    @classmethod
    def check_or_fix_file(cls, file_path: str, *, fix: bool) -> bool:
        """Check and optionally fix values in a single CSV file.

        Args:
            file_path: Path to the CSV file to check or fix
            fix: If True, overwrite the file with fixed values; if False, only check
        Returns:
            True if the file is already valid, False if changes are needed
        """

        is_valid = True
        updated_rows = []
        with open(file_path, "r", newline="", encoding="utf-8") as input_file:
            reader = csv.reader(input_file)
            for row in reader:
                updated_row = []
                for value in row:
                    updated_value = CsvUtil.normalize_value(value)
                    if updated_value != value:
                        is_valid = False
                    updated_row.append(updated_value)
                updated_rows.append(updated_row)

        if fix and not is_valid:
            with open(file_path, "w", newline="", encoding="utf-8") as output_file:
                writer = csv.writer(
                    output_file,
                    delimiter=",",
                    quotechar='"',
                    quoting=csv.QUOTE_MINIMAL,  # noqa
                    lineterminator=os.linesep,
                )
                writer.writerows(updated_rows)
        return is_valid

    @classmethod
    def check_or_fix_format(
        cls,
        *,
        dirs: Sequence[str],
        ext: str,
        fix: bool,
        verbose: bool = False,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> None:
        """Check and optionally fix all CSV format issues in a single pass.

        Combines all format checks: leftover inner quotes, Excel-reformatted dates,
        and a thousand separators in numbers.

        Args:
            dirs: Directories where file search is performed
            ext: File extension to search for without the leading dot (e.g., "csv")
            fix: If True, fix all format issues; if False, only check and report
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        file_paths = FileUtil.enumerate_files(
            dirs=dirs,
            ext=ext,
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        files_with_error = []
        for file_path in file_paths:
            is_valid = cls.check_or_fix_file(file_path, fix=fix)
            if not is_valid:
                files_with_error.append(file_path)

        if files_with_error:
            files_list = "".join([f"    {file}\n" for file in files_with_error])
            if not fix:
                raise RuntimeError(
                    f"Found CSV format issues (quotes, dates, or numbers) in these files.\n"
                    f"Recommended action: run fix_csv_format script to fix.\n{files_list}"
                )
            elif verbose:
                print(f"Corrected CSV format in the following files:\n{files_list}")
        elif verbose:
            files_list = "".join([f"    {x}\n" for x in sorted(file_paths)])
            print(f"Verified CSV format in the following files:\n{files_list}")

    @classmethod
    def check_or_fix_quotes(
        cls,
        *,
        dirs: Sequence[str],
        ext: str,
        apply_fix: bool,
        verbose: bool = False,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> None:
        """Check and optionally fix CSV quoting issues.

        Args:
            dirs: Directories where file search is performed
            ext: File extension to search for without the leading dot (e.g., "csv")
            apply_fix: If True, fix all quoting issues; if False, only check and report
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """
        cls.check_or_fix_format(
            dirs=dirs,
            ext=ext,
            fix=apply_fix,
            verbose=verbose,
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

    @staticmethod
    def _xlsx_path_from_csv(file_path: str) -> str:
        """Derive the xlsx source path from a CSV file path."""
        dir_path = os.path.dirname(file_path)
        basename = os.path.basename(file_path)
        if basename.endswith(".generated.csv"):
            stem = basename.removesuffix(".generated.csv")
        else:
            stem = os.path.splitext(basename)[0]
        xlsx_base = stem.rsplit(".", 1)[0]
        return os.path.join(dir_path, f"{xlsx_base}.xlsx")

    @classmethod
    def _deserialize_row(cls, *, record_type: type, row_dict: dict[str, Any]) -> tuple[RecordMixin, str | None]:
        """Deserialize row into a record with optional dataset.
        Args:
            record_type: Type of the record to deserialize into
            row_dict: Dictionary representing a CSV row
        Returns:
            Tuple of (deserialized record, dataset string or None)
        Raises:
            RuntimeError: If deserialization fails
        """

        # Normalize chars and set None for empty strings
        row_dict = {CharUtil.normalize(k): CharUtil.normalize_or_none(v) for k, v in row_dict.items()}

        # Convert column headers to snake_case field names
        row_dict = {CaseUtil.any_to_snake_case(k) if not k.startswith("_") else k: v for k, v in row_dict.items()}

        # Normalize Excel-modified formats (thousand separators in numbers, locale-specific dates, times and datetimes)
        row_dict = {
            k: (
                CsvUtil.normalize_numeric_str(
                    CsvUtil.normalize_datetime_str(CsvUtil.normalize_time_str(CsvUtil.normalize_date_str(v)))
                )
                if v is not None
                else v
            )
            for k, v in row_dict.items()
        }

        # Extract _dataset before deserialization (not a record field)
        dataset = row_dict.pop("_dataset", None)

        row_dict["_type"] = typename(record_type)

        result = _SERIALIZER.deserialize(row_dict).build()
        return result, dataset
