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
import re


class CsvUtil:
    """Utilities for CSV serialization matching Excel's standard CSV quoting behavior (RFC 4180)."""

    # Characters that trigger quoting in Excel CSV output
    _SPECIAL_CHARS_RE = re.compile(r'[,"\r\n]')

    # ISO-8601 date pattern (yyyy-mm-dd)
    _ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    @classmethod
    def strip_quotes(cls, value: str) -> str:
        """Strip the surrounding double quotes if present, return the argument if not present."""
        if value.startswith('"') and value.endswith('"'):
            # Only if both leading and trailing quote is present
            return value[1:-1]
        else:
            return value

    @classmethod
    def has_quotes(cls, value: str) -> bool:
        """Return True if surrounded by quotes, both leading and trailing quote must be present."""
        return value.startswith('"') and value.endswith('"')

    @classmethod
    def requires_quotes(cls, value: str) -> bool:
        """Return True if quotes are required per Excel's CSV output rules (RFC 4180).

        Excel quotes a value only when it contains a comma, double quote, carriage return, or newline.
        Numbers and dates are NOT quoted (unlike the previous behavior that quoted them to prevent
        Excel from reformatting).
        """

        # Strip the existing surrounding quotes if present
        value = cls.strip_quotes(value)

        # Quote when the value contains special characters that would break CSV parsing
        return bool(cls._SPECIAL_CHARS_RE.search(value))

    @classmethod
    def should_wrap(cls, value: str) -> bool:
        """Return True if quotes are required but not present, False in all other cases."""
        requires_quotes = cls.requires_quotes(value)
        has_quotes = cls.has_quotes(value)
        return requires_quotes and not has_quotes

    @classmethod
    def check_or_fix_quotes(cls, file_path: str, *, apply_fix: bool) -> bool:
        """Check that CSV follows Excel-standard quoting with no unnecessary inner quotes.

        Detects leftover inner quotes from old triple-quoting (e.g. a parsed value of '"1.2"'
        that came from '\"\"\"1.2\"\"\"' in raw CSV). Strips them if apply_fix is True.
        Returns True if the file already matches Excel's quoting, False if changes are needed.
        """

        is_valid = True
        updated_rows = []
        with open(file_path, "r", newline="", encoding="utf-8") as input_file:
            reader = csv.reader(input_file)
            for row in reader:
                updated_row = []
                for value in row:
                    # Strip leftover inner quotes that were added by old triple-quoting logic
                    if cls.has_quotes(value):
                        stripped = cls.strip_quotes(value)
                        is_valid = False
                        updated_row.append(stripped)
                    else:
                        updated_row.append(value)
                updated_rows.append(updated_row)

        # Overwrite only if apply_fix is True and is_valid is False
        if apply_fix and not is_valid:
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
    def normalize_date_str(cls, value: str) -> str:
        """Normalize an Excel-modified date string to ISO-8601 format (yyyy-mm-dd).

        Handles common Excel date formats such as M/D/YYYY, MM/DD/YYYY, and 'Month D, YYYY'.
        Returns the original string if it cannot be recognized as a date.
        """

        value = cls.strip_quotes(value)

        # Already in ISO format
        if cls._ISO_DATE_RE.match(value):
            return value

        # Try dateutil parsing as a fallback for Excel-reformatted dates
        try:
            from dateutil.parser import parse

            parsed = parse(value, dayfirst=False)
            return f"{parsed.year:04}-{parsed.month:02}-{parsed.day:02}"
        except (ValueError, OverflowError):
            return value

    @classmethod
    def normalize_numeric_str(cls, value: str) -> str:
        """Normalize an Excel-modified numeric string by stripping thousand separators.

        Handles formats like '1,234.56' -> '1234.56' and '1,234' -> '1234'.
        Returns the original string if removing commas does not produce a valid number.
        """

        value = cls.strip_quotes(value)

        if "," in value:
            stripped = value.replace(",", "")
            try:
                float(stripped)
                return stripped
            except ValueError:
                return value
        return value
