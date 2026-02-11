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

import pytest
from cl.runtime.serializers.csv_util import CsvUtil


def test_requires_quotes():
    """Test CsvUtil.requires_quotes() matches Excel's CSV quoting rules (RFC 4180)."""

    # Should NOT require quotes - no special characters (comma, double quote, CR, LF)
    no_quote_cases = [
        "",
        "plain text",
        "42",
        "3.14",
        "99%",
        "99.0%",
        "$1",
        "2023-05-21",
        "1m",
        "Not a date 123abc",
        "[Begins from bracket",
        "{Begins from brace",
    ]

    # SHOULD require quotes - contains comma, double quote, CR, or LF
    requires_quotes_cases = [
        "Hello, world!",  # Comma
        'Hello"world!',  # Double quote
        "Hello\nworld!",  # LF
        "Hello\rworld!",  # CR
        "May 1, 2003",  # Comma in date
        "prefix May 1, 2003",  # Comma
    ]

    for case in no_quote_cases:
        assert not CsvUtil.requires_quotes(case), f"Expected requires_quotes to return False for: {case}"

    for case in requires_quotes_cases:
        assert CsvUtil.requires_quotes(case), f"Expected requires_quotes to return True for: {case}"


def test_strip_quotes():
    """Test CsvUtil.strip_quotes() method."""

    assert CsvUtil.strip_quotes('"hello"') == "hello"
    assert CsvUtil.strip_quotes('"1.2"') == "1.2"
    assert CsvUtil.strip_quotes("hello") == "hello"
    assert CsvUtil.strip_quotes('"only_leading') == '"only_leading'
    assert CsvUtil.strip_quotes('""') == ""
    assert CsvUtil.strip_quotes("") == ""


def test_normalize_date_str():
    """Test CsvUtil.normalize_date_str() handles Excel-modified date formats."""

    # Already ISO format - pass through
    assert CsvUtil.normalize_date_str("2023-05-21") == "2023-05-21"

    # Excel-modified formats
    assert CsvUtil.normalize_date_str("5/21/2023") == "2023-05-21"
    assert CsvUtil.normalize_date_str("05/21/2023") == "2023-05-21"
    assert CsvUtil.normalize_date_str("May 21, 2023") == "2023-05-21"

    # With surrounding quotes (backward compat)
    assert CsvUtil.normalize_date_str('"2023-05-21"') == "2023-05-21"

    # Not a date - return as-is
    assert CsvUtil.normalize_date_str("not a date") == "not a date"


def test_normalize_numeric_str():
    """Test CsvUtil.normalize_numeric_str() handles Excel-modified number formats."""

    # With thousand separators
    assert CsvUtil.normalize_numeric_str("1,234.56") == "1234.56"
    assert CsvUtil.normalize_numeric_str("1,234") == "1234"
    assert CsvUtil.normalize_numeric_str("1,234,567") == "1234567"

    # No separators - pass through
    assert CsvUtil.normalize_numeric_str("1234.56") == "1234.56"
    assert CsvUtil.normalize_numeric_str("42") == "42"

    # Not a number with commas - return as-is
    assert CsvUtil.normalize_numeric_str("hello, world") == "hello, world"

    # With surrounding quotes (backward compat)
    assert CsvUtil.normalize_numeric_str('"1,234"') == "1234"


def test_check_or_fix_file(work_dir_fixture):
    """Test CsvUtil.check_or_fix_quotes() detects and strips leftover inner quotes."""

    # valid.csv should already match Excel-standard quoting (no inner quotes)
    assert CsvUtil.check_or_fix_quotes("valid.csv", apply_fix=False)


if __name__ == "__main__":
    pytest.main([__file__])
