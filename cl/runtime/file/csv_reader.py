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
from typing import Any
from typing import Callable
from typing import Sequence
from cl.runtime.file.file_util import FileUtil
from cl.runtime.file.reader import Reader
from cl.runtime.primitive.char_util import CharUtil
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.serializers.csv_util import CsvUtil
from cl.runtime.serializers.data_serializers import DataSerializers

_SERIALIZER = DataSerializers.FOR_CSV


class CsvReader(Reader):
    """Helper class for working with CSV files."""

    def load_all(
        self,
        *,
        dirs: Sequence[str],
        ext: str,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> tuple[RecordMixin]:

        file_paths = FileUtil.enumerate_files(
            dirs=dirs,
            ext=ext,
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        # Iterate over files
        result = []
        for file_path in file_paths:
            try:
                # Determine record type from filename
                record_type = FileUtil.get_type_from_filename(file_path)

                with open(file_path, mode="r", encoding="utf-8") as file:

                    # The reader is an iterable of row dicts
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

                    # Deserialize rows into records and add to the result
                    loaded = [
                        self._deserialize_row(record_type=record_type, row_dict=row_dict) for row_dict in row_dicts
                    ]
                    result.extend(loaded)
            except Exception as e:
                raise RuntimeError(f"Failed to load CSV file {file_path}. Error: {e}") from e

        # Convert to tuple and return
        return tuple(result)

    @classmethod
    def _check_or_fix_file(cls, file_path: str, *, fix: bool, value_fn: Callable[[str], str]) -> bool:
        """Check and optionally fix values in a single CSV file.

        Args:
            file_path: Path to the CSV file to check or fix
            fix: If True, overwrite the file with fixed values; if False, only check
            value_fn: Function that takes a cell value and returns the normalized value
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
                    updated_value = value_fn(value)
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
                    quoting=csv.QUOTE_MINIMAL,
                    lineterminator="\n",
                )
                writer.writerows(updated_rows)
        return is_valid

    @classmethod
    def _run_file_check(
        cls,
        *,
        dirs: Sequence[str],
        ext: str,
        fix: bool,
        verbose: bool = False,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
        value_fn: Callable[[str], str],
        error_description: str,
    ) -> None:
        """Common logic for directory-level check_or_fix methods.

        Args:
            dirs: Directories where file search is performed
            ext: File extension to search for without the leading dot (e.g., "csv")
            fix: If True, modify CSV files to fix the detected issues; if False, only check
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
            value_fn: Function that takes a cell value and returns the normalized value
            error_description: Description of the format issue for error/verbose messages
        """

        file_paths = FileUtil.enumerate_files(
            dirs=dirs,
            ext=ext,
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        files_with_error = []
        for file_path in file_paths:
            is_valid = cls._check_or_fix_file(file_path, fix=fix, value_fn=value_fn)
            if not is_valid:
                files_with_error.append(file_path)

        if files_with_error:
            files_list = "".join([f"    {file}\n" for file in files_with_error])
            msg = (
                f"{error_description}\n"
                f"RECOMMENDED ACTION: Run fix_csv_format script to fix.\n{files_list}"
            )
            if not fix:
                raise RuntimeError(msg)
            elif verbose:
                print(msg)
        elif verbose:
            files_list = "".join([f"    {x}\n" for x in sorted(file_paths)])
            print(f"Verified CSV format in the following files:\n{files_list}")

    @classmethod
    def check_or_fix_quotes(
        cls,
        *,
        dirs: Sequence[str],
        ext: str,
        fix: bool,
        verbose: bool = False,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> None:
        """Check CSV files for unnecessary inner quotes leftover from old triple-quoting.

        Args:
            dirs: Directories where file search is performed
            ext: File extension to search for without the leading dot (e.g., "csv")
            fix: If True, strip the leftover inner quotes; if False, only check and report
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        cls._run_file_check(
            dirs=dirs,
            ext=ext,
            fix=fix,
            verbose=verbose,
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
            value_fn=CsvUtil.strip_quotes,
            error_description="Found values with unnecessary inner quotes (leftover from old triple-quoting).",
        )

    @classmethod
    def check_or_fix_dates(
        cls,
        *,
        dirs: Sequence[str],
        ext: str,
        fix: bool,
        verbose: bool = False,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> None:
        """Check CSV files for Excel-reformatted dates not in ISO-8601 format.

        Args:
            dirs: Directories where file search is performed
            ext: File extension to search for without the leading dot (e.g., "csv")
            fix: If True, normalize dates to ISO-8601 (yyyy-mm-dd); if False, only check and report
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        cls._run_file_check(
            dirs=dirs,
            ext=ext,
            fix=fix,
            verbose=verbose,
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
            value_fn=CsvUtil.normalize_date_str,
            error_description="Found date values not in ISO-8601 format.",
        )

    @classmethod
    def check_or_fix_numbers(
        cls,
        *,
        dirs: Sequence[str],
        ext: str,
        fix: bool,
        verbose: bool = False,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> None:
        """Check CSV files for numeric values with thousand separators.

        Args:
            dirs: Directories where file search is performed
            ext: File extension to search for without the leading dot (e.g., "csv")
            fix: If True, strip thousand separators; if False, only check and report
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        cls._run_file_check(
            dirs=dirs,
            ext=ext,
            fix=fix,
            verbose=verbose,
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
            value_fn=CsvUtil.normalize_numeric_str,
            error_description="Found numeric values with thousand separators.",
        )

    @classmethod
    def check_or_fix_csv_format(
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
        and thousand separators in numbers.

        Args:
            dirs: Directories where file search is performed
            ext: File extension to search for without the leading dot (e.g., "csv")
            fix: If True, fix all format issues; if False, only check and report
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        cls._run_file_check(
            dirs=dirs,
            ext=ext,
            fix=fix,
            verbose=verbose,
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
            value_fn=CsvUtil.normalize_value,
            error_description="Found CSV format issues (quotes, dates, or numbers).",
        )

    @classmethod
    def _deserialize_row(cls, *, record_type: type, row_dict: dict[str, Any]) -> RecordMixin:
        """Deserialize row into a record.
        Args:
            record_type: Type of the record to deserialize into
            row_dict: Dictionary representing a CSV row
        Returns:
            Deserialized record
        Raises:
            RuntimeError: If deserialization fails
        """

        # Normalize chars and set None for empty strings
        row_dict = {CharUtil.normalize(k): CharUtil.normalize_or_none(v) for k, v in row_dict.items()}

        # Normalize Excel-modified formats (thousand separators in numbers, locale-specific dates)
        row_dict = {
            k: CsvUtil.normalize_numeric_str(CsvUtil.normalize_date_str(v)) if v is not None else v
            for k, v in row_dict.items()
        }

        row_dict["_type"] = typename(record_type)

        result = _SERIALIZER.deserialize(row_dict).build()
        return result
