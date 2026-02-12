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


# --- has_quotes ---


def test_has_quotes_both():
    """Value with both leading and trailing double quote."""
    assert CsvUtil.has_quotes('"hello"')
    assert CsvUtil.has_quotes('"1.2"')
    assert CsvUtil.has_quotes('"May 1, 2003"')


def test_has_quotes_empty_quotes():
    """Two double quotes (empty quoted value)."""
    assert CsvUtil.has_quotes('""')


def test_has_quotes_single_char():
    """Single double-quote character matches both leading and trailing."""
    assert CsvUtil.has_quotes('"')


def test_has_quotes_no_quotes():
    """Values without surrounding quotes."""
    assert not CsvUtil.has_quotes("hello")
    assert not CsvUtil.has_quotes("")
    assert not CsvUtil.has_quotes("42")


def test_has_quotes_leading_only():
    """Only a leading double quote, no trailing."""
    assert not CsvUtil.has_quotes('"hello')


def test_has_quotes_trailing_only():
    """Only a trailing double quote, no leading."""
    assert not CsvUtil.has_quotes('hello"')


def test_has_quotes_embedded():
    """Double quotes embedded in the middle, not surrounding."""
    assert not CsvUtil.has_quotes('he"llo')
    assert not CsvUtil.has_quotes('he""llo')


# --- strip_quotes ---


def test_strip_quotes_both():
    """Strip surrounding quotes from normally quoted values."""
    assert CsvUtil.strip_quotes('"hello"') == "hello"
    assert CsvUtil.strip_quotes('"1.2"') == "1.2"
    assert CsvUtil.strip_quotes('"May 1, 2003"') == "May 1, 2003"


def test_strip_quotes_empty():
    """Two double quotes strip to empty string."""
    assert CsvUtil.strip_quotes('""') == ""


def test_strip_quotes_nested():
    """Surrounding quotes stripped, inner quotes remain."""
    assert CsvUtil.strip_quotes('""hello""') == '"hello"'


def test_strip_quotes_no_quotes():
    """Values without surrounding quotes pass through unchanged."""
    assert CsvUtil.strip_quotes("hello") == "hello"
    assert CsvUtil.strip_quotes("") == ""
    assert CsvUtil.strip_quotes("42") == "42"


def test_strip_quotes_leading_only():
    """Only leading quote - not stripped (both required)."""
    assert CsvUtil.strip_quotes('"hello') == '"hello'


def test_strip_quotes_trailing_only():
    """Only trailing quote - not stripped (both required)."""
    assert CsvUtil.strip_quotes('hello"') == 'hello"'


def test_strip_quotes_embedded():
    """Embedded quotes - not stripped (not surrounding)."""
    assert CsvUtil.strip_quotes('he"llo') == 'he"llo'


# --- requires_quotes (Excel/RFC 4180) ---


def test_requires_quotes_plain_text():
    """Plain text without special characters does not require quotes."""
    assert not CsvUtil.requires_quotes("")
    assert not CsvUtil.requires_quotes("plain text")
    assert not CsvUtil.requires_quotes("hello world")


def test_requires_quotes_integers():
    """Integers do not require quotes (Excel writes them unquoted)."""
    assert not CsvUtil.requires_quotes("0")
    assert not CsvUtil.requires_quotes("42")
    assert not CsvUtil.requires_quotes("-1")
    assert not CsvUtil.requires_quotes("007")


def test_requires_quotes_floats():
    """Floats do not require quotes."""
    assert not CsvUtil.requires_quotes("3.14")
    assert not CsvUtil.requires_quotes("-0.5")
    assert not CsvUtil.requires_quotes("1.0")
    assert not CsvUtil.requires_quotes(".5")


def test_requires_quotes_percentages_currency():
    """Percentages and currency symbols do not require quotes."""
    assert not CsvUtil.requires_quotes("99%")
    assert not CsvUtil.requires_quotes("99.0%")
    assert not CsvUtil.requires_quotes("$1")
    assert not CsvUtil.requires_quotes("$100.00")


def test_requires_quotes_iso_dates():
    """ISO format dates do not require quotes (no special chars)."""
    assert not CsvUtil.requires_quotes("2023-05-21")
    assert not CsvUtil.requires_quotes("2023-01-01")


def test_requires_quotes_scientific_notation():
    """Scientific notation does not require quotes."""
    assert not CsvUtil.requires_quotes("1.23E+14")
    assert not CsvUtil.requires_quotes("1e10")
    assert not CsvUtil.requires_quotes("5E-3")


def test_requires_quotes_alphanumeric():
    """Alphanumeric text without special chars does not require quotes."""
    assert not CsvUtil.requires_quotes("1m")
    assert not CsvUtil.requires_quotes("abc123")
    assert not CsvUtil.requires_quotes("Not a date 123abc")


def test_requires_quotes_brackets_braces():
    """Values starting with brackets/braces do not require quotes (no special chars)."""
    assert not CsvUtil.requires_quotes("[Begins from bracket")
    assert not CsvUtil.requires_quotes("{Begins from brace")


def test_requires_quotes_comma():
    """Values containing comma require quotes."""
    assert CsvUtil.requires_quotes("Hello, world!")
    assert CsvUtil.requires_quotes("May 1, 2003")
    assert CsvUtil.requires_quotes("prefix May 1, 2003")
    assert CsvUtil.requires_quotes("a,b")
    assert CsvUtil.requires_quotes(",")


def test_requires_quotes_double_quote():
    """Values containing double quotes require quotes."""
    assert CsvUtil.requires_quotes('Hello"world!')
    assert CsvUtil.requires_quotes('he"llo')


def test_requires_quotes_newline():
    """Values containing LF or CR require quotes."""
    assert CsvUtil.requires_quotes("Hello\nworld!")
    assert CsvUtil.requires_quotes("Hello\rworld!")
    assert CsvUtil.requires_quotes("line1\r\nline2")


def test_requires_quotes_leading_double_quote():
    """Value with only a leading double quote contains a quote character, requires quoting.

    In CSV, a cell containing the text ("hello) is encoded as '\"\"\"hello' by csv.writer.
    After csv.reader, we get the string '"hello'.
    """
    assert CsvUtil.requires_quotes('"hello')


def test_requires_quotes_trailing_double_quote():
    """Value with only a trailing double quote contains a quote character, requires quoting.

    In CSV, a cell containing text (hello\") is encoded as '\"hello\"\"\"' by csv.writer.
    After csv.reader, we get 'hello\"'.
    """
    assert CsvUtil.requires_quotes('hello"')


def test_requires_quotes_both_surrounding():
    """Value with both leading and trailing double quotes (like old triple-quoted values).

    After csv.reader parses triple-quoted '\"\"\"1.2\"\"\"', we get '\"1.2\"'.
    strip_quotes reduces to '1.2' which has no special chars -> False.
    """
    assert not CsvUtil.requires_quotes('"1.2"')
    assert not CsvUtil.requires_quotes('"hello"')
    assert not CsvUtil.requires_quotes('"2023-05-21"')


def test_requires_quotes_surrounding_with_special_inside():
    """Value with surrounding quotes AND special chars inside still requires quotes.

    strip_quotes('"May 1, 2003"') gives 'May 1, 2003' which has comma -> True.
    """
    assert CsvUtil.requires_quotes('"May 1, 2003"')
    assert CsvUtil.requires_quotes('"line1\nline2"')


def test_requires_quotes_thousand_separators():
    """Numbers with en-US thousand separators contain commas, so require quotes."""
    assert CsvUtil.requires_quotes("1,234")
    assert CsvUtil.requires_quotes("1,234.56")
    assert CsvUtil.requires_quotes("1,234,567")


def test_requires_quotes_whitespace():
    """Whitespace-only values do not require quotes (Excel behavior)."""
    assert not CsvUtil.requires_quotes(" ")
    assert not CsvUtil.requires_quotes("  hello  ")


# --- should_wrap ---


def test_should_wrap_needs_wrapping():
    """Value with comma but no surrounding quotes needs wrapping."""
    assert CsvUtil.should_wrap("Hello, world!")
    assert CsvUtil.should_wrap('he"llo')


def test_should_wrap_already_wrapped():
    """Value with surrounding quotes AND inner comma: requires_quotes=True, has_quotes=True -> False."""
    assert not CsvUtil.should_wrap('"May 1, 2003"')


def test_should_wrap_not_needed():
    """Values that do not need quoting at all."""
    assert not CsvUtil.should_wrap("42")
    assert not CsvUtil.should_wrap("hello")
    assert not CsvUtil.should_wrap("2023-05-21")
    assert not CsvUtil.should_wrap("")


def test_should_wrap_old_triple_quoted():
    """Old triple-quoted values: surrounding quotes present, inner content is clean -> False."""
    assert not CsvUtil.should_wrap('"1.2"')
    assert not CsvUtil.should_wrap('"42"')


# --- normalize_date_str ---


def test_normalize_date_iso_passthrough():
    """Already in ISO-8601 format - passes through unchanged."""
    assert CsvUtil.normalize_date_str("2023-05-21") == "2023-05-21"
    assert CsvUtil.normalize_date_str("2000-01-01") == "2000-01-01"
    assert CsvUtil.normalize_date_str("1999-12-31") == "1999-12-31"


def test_normalize_date_us_short():
    """Excel en-US short date: M/D/YYYY."""
    assert CsvUtil.normalize_date_str("5/21/2023") == "2023-05-21"
    assert CsvUtil.normalize_date_str("1/1/2000") == "2000-01-01"
    assert CsvUtil.normalize_date_str("12/31/1999") == "1999-12-31"


def test_normalize_date_us_padded():
    """Excel en-US padded date: MM/DD/YYYY."""
    assert CsvUtil.normalize_date_str("05/21/2023") == "2023-05-21"
    assert CsvUtil.normalize_date_str("01/01/2000") == "2000-01-01"


def test_normalize_date_month_name():
    """Excel long date: Month D, YYYY."""
    assert CsvUtil.normalize_date_str("May 21, 2023") == "2023-05-21"
    assert CsvUtil.normalize_date_str("January 1, 2000") == "2000-01-01"
    assert CsvUtil.normalize_date_str("December 31, 1999") == "1999-12-31"


def test_normalize_date_abbreviated_month():
    """Excel abbreviated month: Mon D, YYYY or D-Mon-YYYY."""
    assert CsvUtil.normalize_date_str("May 21, 2023") == "2023-05-21"
    assert CsvUtil.normalize_date_str("Jan 1, 2000") == "2000-01-01"
    assert CsvUtil.normalize_date_str("21-May-2023") == "2023-05-21"


def test_normalize_date_two_digit_year():
    """Excel en-US with two-digit year: M/D/YY."""
    assert CsvUtil.normalize_date_str("5/21/23") == "2023-05-21"
    assert CsvUtil.normalize_date_str("1/1/00") == "2000-01-01"


def test_normalize_date_backward_compat_quoted():
    """Old triple-quoted dates have surrounding quotes that should be stripped."""
    assert CsvUtil.normalize_date_str('"2023-05-21"') == "2023-05-21"
    assert CsvUtil.normalize_date_str('"5/21/2023"') == "2023-05-21"


def test_normalize_date_not_a_date():
    """Non-date strings return as-is."""
    assert CsvUtil.normalize_date_str("not a date") == "not a date"
    assert CsvUtil.normalize_date_str("") == ""
    assert CsvUtil.normalize_date_str("42") == "42"
    assert CsvUtil.normalize_date_str("hello world") == "hello world"
    assert CsvUtil.normalize_date_str("3.14") == "3.14"


# --- normalize_numeric_str ---


def test_normalize_numeric_thousand_separators():
    """Excel en-US thousand separators: comma every 3 digits."""
    assert CsvUtil.normalize_numeric_str("1,234") == "1234"
    assert CsvUtil.normalize_numeric_str("1,234.56") == "1234.56"
    assert CsvUtil.normalize_numeric_str("1,234,567") == "1234567"
    assert CsvUtil.normalize_numeric_str("1,234,567.89") == "1234567.89"


def test_normalize_numeric_negative_with_separators():
    """Negative numbers with thousand separators."""
    assert CsvUtil.normalize_numeric_str("-1,234") == "-1234"
    assert CsvUtil.normalize_numeric_str("-1,234.56") == "-1234.56"


def test_normalize_numeric_large_numbers():
    """Large numbers with multiple separator groups."""
    assert CsvUtil.normalize_numeric_str("10,000,000") == "10000000"
    assert CsvUtil.normalize_numeric_str("1,000,000,000") == "1000000000"


def test_normalize_numeric_no_separators():
    """Numbers without thousand separators pass through unchanged."""
    assert CsvUtil.normalize_numeric_str("42") == "42"
    assert CsvUtil.normalize_numeric_str("1234.56") == "1234.56"
    assert CsvUtil.normalize_numeric_str("0") == "0"
    assert CsvUtil.normalize_numeric_str("-1") == "-1"
    assert CsvUtil.normalize_numeric_str("3.14") == "3.14"
    assert CsvUtil.normalize_numeric_str(".5") == ".5"


def test_normalize_numeric_scientific_notation():
    """Scientific notation has no commas, passes through."""
    assert CsvUtil.normalize_numeric_str("1.23E+14") == "1.23E+14"
    assert CsvUtil.normalize_numeric_str("5e-3") == "5e-3"


def test_normalize_numeric_text_with_commas():
    """Text containing commas that is NOT a valid number after removal."""
    assert CsvUtil.normalize_numeric_str("hello, world") == "hello, world"
    assert CsvUtil.normalize_numeric_str("May 1, 2003") == "May 1, 2003"
    assert CsvUtil.normalize_numeric_str("a,b,c") == "a,b,c"


def test_normalize_numeric_backward_compat_quoted():
    """Old triple-quoted numbers have surrounding quotes that should be stripped."""
    assert CsvUtil.normalize_numeric_str('"1,234"') == "1234"
    assert CsvUtil.normalize_numeric_str('"42"') == "42"


def test_normalize_numeric_empty_and_whitespace():
    """Empty and whitespace values pass through."""
    assert CsvUtil.normalize_numeric_str("") == ""
    assert CsvUtil.normalize_numeric_str(" ") == " "


def test_normalize_numeric_percentage():
    """Percentage strings are not valid floats, pass through unchanged."""
    assert CsvUtil.normalize_numeric_str("50%") == "50%"


# --- check_or_fix_quotes (uses work_dir_fixture, directory must match function name) ---


def test_check_or_fix_file(work_dir_fixture):
    """Test CsvUtil.check_or_fix_quotes() detects and strips leftover inner quotes.

    Fixture files:
    - valid.csv: Excel-standard format (no inner quotes) -> passes validation
    - unescaped_date.csv: has '\"\"\"1.2\"\"\"' (triple-quoted number) -> csv.reader gives '\"1.2\"' -> invalid
    - unescaped_float.csv: has '\"\"\"May 1, 2003\"\"\"' (triple-quoted date) -> csv.reader gives '\"May 1, 2003\"' -> invalid
    """

    # File already in Excel-standard format passes
    assert CsvUtil.check_or_fix_quotes("valid.csv", fix=False)

    # File with old triple-quoted number is detected as invalid (leftover inner quotes)
    assert not CsvUtil.check_or_fix_quotes("unescaped_date.csv", fix=False)

    # File with old triple-quoted date is detected as invalid (leftover inner quotes)
    assert not CsvUtil.check_or_fix_quotes("unescaped_float.csv", fix=False)


if __name__ == "__main__":
    pytest.main([__file__])
