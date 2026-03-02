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

import re


class CsvUtil:
    """Utilities for CSV serialization matching Excel's standard CSV quoting behavior (RFC 4180)."""

    # Characters that trigger quoting in Excel CSV output
    _SPECIAL_CHARS_RE = re.compile(r'[,"\r\n]')

    # ISO-8601 date pattern (yyyy-mm-dd)
    _ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    # Compact date pattern (yyyymmdd)
    _COMPACT_DATE_RE = re.compile(r"^\d{8}$")

    # ISO-8601 datetime pattern (yyyy-mm-ddThh:mm:ss.fffZ)
    _ISO_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

    # Compact datetime pattern (yyyymmdd-hhmmssfff)
    _COMPACT_DATETIME_RE = re.compile(r"^\d{8}-\d{9}$")

    # ISO-8601 time pattern (hh:mm:ss.fff)
    _ISO_TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}$")

    # Compact time pattern (hhmmssfff)
    _COMPACT_TIME_RE = re.compile(r"^\d{9}$")

    # Pattern for values that look like dates (contain / or month names)
    _DATE_LIKE_RE = re.compile(
        r"(?:\d{1,2}/\d{1,2}/|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))",
        re.IGNORECASE,
    )

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
    def normalize_date_str(cls, value: str) -> str:
        """Normalize a date string to compact format (yyyymmdd).

        Handles common Excel en-US date formats such as M/D/YYYY, MM/DD/YYYY, and 'Month D, YYYY'.
        Also converts old ISO-8601 format (yyyy-mm-dd) to compact format.
        Returns the original string if it cannot be recognized as a date.
        """

        value = cls.strip_quotes(value)

        # Already in compact format
        if cls._COMPACT_DATE_RE.match(value):
            return value

        # Old ISO format - convert to compact
        if cls._ISO_DATE_RE.match(value):
            return value.replace("-", "")

        # Only attempt parsing if the value looks like a date (contains / separator or month name)
        # This prevents dateutil from interpreting bare numbers like "42" as dates
        if not cls._DATE_LIKE_RE.search(value):
            return value

        # Require at least 2 numeric groups to avoid parsing partial dates like "Aug 2021" (month-year only)
        if len(re.findall(r"\d+", value)) < 2:
            return value

        # Try dateutil parsing as a fallback for Excel-reformatted dates
        try:
            from dateutil.parser import parse

            parsed = parse(value, dayfirst=False)
            return f"{parsed.year:04}{parsed.month:02}{parsed.day:02}"
        except (ValueError, OverflowError):
            return value

    @classmethod
    def normalize_datetime_str(cls, value: str) -> str:
        """Normalize a datetime string to compact format (yyyymmdd-hhmmssfff).

        Converts old ISO-8601 format (yyyy-mm-ddThh:mm:ss.fffZ) to compact format.
        Returns the original string if it cannot be recognized as a datetime.
        """

        value = cls.strip_quotes(value)

        # Already in compact format
        if cls._COMPACT_DATETIME_RE.match(value):
            return value

        # Old ISO format - convert to compact
        if cls._ISO_DATETIME_RE.match(value):
            return (
                value[0:4] + value[5:7] + value[8:10] + "-" + value[11:13] + value[14:16] + value[17:19] + value[20:23]
            )

        return value

    @classmethod
    def normalize_time_str(cls, value: str) -> str:
        """Normalize a time string to compact format (hhmmssfff).

        Converts old ISO-8601 format (hh:mm:ss.fff) to compact format.
        Returns the original string if it cannot be recognized as a time.
        """

        value = cls.strip_quotes(value)

        # Already in compact format
        if cls._COMPACT_TIME_RE.match(value):
            return value

        # Old ISO format - convert to compact by removing separators
        if cls._ISO_TIME_RE.match(value):
            return value[0:2] + value[3:5] + value[6:8] + value[9:12]

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

    @classmethod
    def normalize_value(cls, value: str) -> str:
        """Apply all normalizations to a CSV cell value: strip inner quotes, dates, times, datetimes, and numbers."""
        value = cls.strip_quotes(value)
        value = cls.normalize_date_str(value)
        value = cls.normalize_time_str(value)
        value = cls.normalize_datetime_str(value)
        value = cls.normalize_numeric_str(value)
        return value
