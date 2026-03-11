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
from cl.runtime.primitive.case_util import CaseUtil


def check_raises_error(check_function, value, expected_message):
    with pytest.raises(RuntimeError) as exc_info:
        check_function(value)
    assert str(exc_info.value) == expected_message


def test_pascal_to_snake_case():
    test_cases = (
        # Rule: insert _ after lowercase letter followed by uppercase letter or digit
        # All-uppercase segments produce no underscores
        ("A2", "a2"),
        ("AB2", "ab2"),
        ("AB2D", "ab2d"),
        ("ABC2D", "abc2d"),
        ("ABC2", "abc2"),
        ("ABC2DEF", "abc2def"),
        ("AB2CD3EF", "ab2cd3ef"),
        # Lowercase-to-digit and lowercase-to-uppercase boundaries
        ("Abc2", "abc_2"),
        ("Abc2D", "abc_2d"),
        ("Abc2DEF", "abc_2def"),
        ("Abc2D3", "abc_2d3"),
        ("Abc123D", "abc_123d"),
        ("Abc123DEF", "abc_123def"),
        ("Something2D", "something_2d"),
        ("Something2DAND", "something_2dand"),
        ("SomethingT0", "something_t0"),
        ("SomethingT0AND", "something_t0and"),
        ("Something2ABC", "something_2abc"),
        ("AbcT0", "abc_t0"),
        # From PascalCase without dot delimiter
        ("AbcDef", "abc_def"),
        # From PascalCase with dot delimiter
        ("Abc.Def", "abc.def"),
        ("AbcDef.Xyz", "abc_def.xyz"),
        ("AbcDef.UvwXyz", "abc_def.uvw_xyz"),
    )

    for input_value, expected in test_cases:
        assert CaseUtil.pascal_to_snake_case(input_value) == expected


def test_snake_to_pascal_case():
    test_cases = (
        # From snake_case with digits
        ("a2", "A2"),
        ("ab2", "AB2"),
        ("ab2d", "AB2D"),
        ("abc2d", "ABC2D"),
        ("abc2", "ABC2"),
        ("abc_2", "Abc2"),
        ("abc_2d", "Abc2D"),
        ("abc_2def", "Abc2DEF"),
        ("abc_2d3", "Abc2D3"),
        ("abc_123def", "Abc123DEF"),
        # From snake_case without dot delimiter
        ("abc_def", "AbcDef"),
        # From snake_case with dot delimiter
        ("abc.def", "Abc.Def"),
        ("abc_def.xyz", "AbcDef.Xyz"),
        ("abc_def.uvw_xyz", "AbcDef.UvwXyz"),
        ("node_id", "NodeId"),
    )

    for input_value, expected in test_cases:
        assert CaseUtil.snake_to_pascal_case(input_value) == expected


def test_pascal_to_title_case():
    test_cases = (
        ("A2", "A2"),
        ("AB2", "AB2"),
        ("AB2D", "AB2D"),
        ("ABC2D", "ABC2D"),
        ("ABC2DEF", "ABC2DEF"),
        ("AB2CD3EF", "AB2CD3EF"),
        ("Abc2", "Abc 2"),
        ("Abc2D", "Abc 2D"),
        ("Abc2DEF", "Abc 2DEF"),
        ("AbcT0", "Abc T0"),
    )

    for input_value, expected in test_cases:
        assert CaseUtil.pascal_to_title_case(input_value) == expected


def test_upper_to_snake_case():
    """Test for case conversion from UPPER_CASE to snake_case."""

    # From UPPER_CASE without dot delimiter
    assert CaseUtil.upper_to_snake_case("ABC_DEF") == "abc_def"

    # From UPPER_CASE with dot delimiter
    assert CaseUtil.upper_to_snake_case("ABC_DEF.XYZ") == "abc_def.xyz"


def test_upper_to_pascal_case():
    """Test for case conversion from UPPER_CASE to PascalCase."""

    # From UPPER_CASE without dot delimiter
    assert CaseUtil.upper_to_pascal_case("ABC_DEF") == "AbcDef"

    # From UPPER_CASE with dot delimiter
    assert CaseUtil.upper_to_pascal_case("ABC_DEF.XYZ") == "AbcDef.Xyz"


def test_pascal_to_upper_case():
    """Test for case conversion from PascalCase to UPPER_CASE."""

    # From UPPER_CASE without dot delimiter
    assert CaseUtil.pascal_to_upper_case("AbcDef") == "ABC_DEF"

    # From UPPER_CASE with dot delimiter
    assert CaseUtil.pascal_to_upper_case("AbcDef.Xyz") == "ABC_DEF.XYZ"


def test_check_snake_case():
    # Valid cases
    CaseUtil.check_snake_case("valid_snake_case_1")
    CaseUtil.check_snake_case("another_valid_case_2026")
    CaseUtil.check_snake_case("valid_snake_case2")
    CaseUtil.check_snake_case("ab2d")

    # Invalid cases
    check_raises_error(
        CaseUtil.check_snake_case,
        "invalid snake case",
        "String invalid snake case is not snake_case because it contains a space.",
    )
    check_raises_error(
        CaseUtil.check_snake_case,
        "InvalidSnakeCase",
        "String InvalidSnakeCase is not snake_case because it contains an uppercase character.",
    )
    check_raises_error(
        CaseUtil.check_snake_case,
        "invalid__snake_case",
        "String invalid__snake_case is not snake_case because it contains a doubled underscore.",
    )
    check_raises_error(
        CaseUtil.check_snake_case,
        "invalid_snake_case_1_2",
        "String invalid_snake_case_1_2 is not snake_case because it does not follow the rule "
        "for separators in front and between digits.",
    )

    # Invalid round-trip: digit-starting segment followed by another segment
    for v in ("abc_2d_ef", "abc_2d_3", "another_valid_3d_case_2", "another_valid_3dcase_2"):
        with pytest.raises(RuntimeError, match="does not round-trip"):
            CaseUtil.check_snake_case(v)


def test_check_pascal_case():
    # Valid cases
    CaseUtil.check_pascal_case("ValidPascalCase")
    CaseUtil.check_pascal_case("AnotherValidPascalCase")
    CaseUtil.check_pascal_case("AnotherValidPascalCaseWithDigits2")
    CaseUtil.check_pascal_case("ABC2D")
    CaseUtil.check_pascal_case("ABC2DEF")
    CaseUtil.check_pascal_case("AB2CD3EF")

    # Invalid format
    check_raises_error(
        CaseUtil.check_pascal_case,
        "Invalid Pascal Case",
        "String Invalid Pascal Case is not PascalCase because it contains a space.",
    )
    check_raises_error(
        CaseUtil.check_pascal_case,
        "invalid_pascal_case",
        "String 'invalid_pascal_case' is not 'PascalCase' because it contains non-alphanumeric characters: '_'",
    )
    check_raises_error(
        CaseUtil.check_pascal_case,
        "invalidPascalcase",
        "String invalidPascalcase is not PascalCase because the first letter is lowercase.",
    )

    # Invalid round-trip: consecutive uppercase without digits
    for v in ("ABC", "ABCDef"):
        with pytest.raises(RuntimeError, match="does not round-trip"):
            CaseUtil.check_pascal_case(v)

    # Invalid round-trip: mixed case in segment containing digits
    for v in ("ABC2Def", "AB2CD3Ef", "ABC2DEf", "AB2DEf", "Something2DAnd", "A2a", "Abc2dEf"):
        with pytest.raises(RuntimeError, match="does not round-trip"):
            CaseUtil.check_pascal_case(v)


def test_check_title_case():
    # Valid cases
    CaseUtil.check_title_case("Title Case Example 1")
    CaseUtil.check_title_case("Another Example 2")

    # Invalid cases
    check_raises_error(
        CaseUtil.check_title_case,
        "invalid_title_case",
        "String 'invalid_title_case' is not 'Title Case' because it contains non-alphanumeric characters: '_'",
    )
    check_raises_error(
        CaseUtil.check_title_case,
        "invalid Title Case",
        "String invalid Title Case is not Title Case because the first letter is lowercase.",
    )
    check_raises_error(
        CaseUtil.check_title_case,
        "Invalid Title Case2",
        "String Invalid Title Case2 is not Title Case because it does not follow the rule "
        "for separators in front of digits.",
    )


def test_check_upper_case():
    # Valid cases
    CaseUtil.check_upper_case("VALID_UPPER_CASE_1")
    CaseUtil.check_upper_case("UPPER_CASE_3DEXAMPLE2")
    CaseUtil.check_upper_case("UPPER_CASE_3DEXAMPLE23")
    CaseUtil.check_upper_case("UPPER_CASE2")
    CaseUtil.check_upper_case("AB2D")

    # Invalid cases
    check_raises_error(
        CaseUtil.check_upper_case,
        "Invalid_UPPER_CASE",
        "String Invalid_UPPER_CASE is not UPPER_CASE because it contains a lowercase character.",
    )
    check_raises_error(
        CaseUtil.check_upper_case,
        "UPPER_CASE example",
        "String UPPER_CASE example is not UPPER_CASE because it contains a space.",
    )
    check_raises_error(
        CaseUtil.check_upper_case,
        "UPPER_CASE_2_3",
        "String UPPER_CASE_2_3 is not UPPER_CASE because it does not follow the rule "
        "for separators in front and between digits.",
    )

    # Invalid round-trip: digit-starting segment followed by another segment
    for v in ("ABC_2D_EF", "ABC_2D_3", "UPPER_CASE_3D_EXAMPLE_2", "UPPER_CASE_3DEXAMPLE_2", "UPPER_CASE_3DEXAMPLE_23"):
        with pytest.raises(RuntimeError, match="does not round-trip"):
            CaseUtil.check_upper_case(v)


def test_round_trip_conversions():
    pascal_to_snake_case_test_cases = (
        # All-uppercase segments (no underscores inserted)
        ("A2", "a2"),
        ("AB2", "ab2"),
        ("AB2D", "ab2d"),
        ("ABC2D", "abc2d"),
        ("ABC2", "abc2"),
        # Consecutive uppercase before multiple digit groups
        ("AB2CD3EF", "ab2cd3ef"),
        # Lowercase-to-digit and lowercase-to-uppercase boundaries
        ("Abc2", "abc_2"),
        ("Abc2D", "abc_2d"),
        ("Abc2D3", "abc_2d3"),
        ("Abc2DEF", "abc_2def"),
        ("Abc12", "abc_12"),
        ("Abc123DEF", "abc_123def"),
        ("Something2D", "something_2d"),
        ("Something2ABC", "something_2abc"),
        ("Something2DAND", "something_2dand"),
        ("SomethingT0", "something_t0"),
        ("SomethingT0AND", "something_t0and"),
        ("AbcT0", "abc_t0"),
        # From PascalCase without dot delimiter
        ("AbcDef", "abc_def"),
        # From PascalCase with dot delimiter
        ("Abc.Def", "abc.def"),
        ("AbcDef.Xyz", "abc_def.xyz"),
        ("AbcDef.UvwXyz", "abc_def.uvw_xyz"),
    )
    snake_to_upper_case_test_cases = (
        # From snake_case with digits
        ("a2", "A2"),
        ("ab2", "AB2"),
        ("ab2d", "AB2D"),
        ("abc2d", "ABC2D"),
        ("abc2", "ABC2"),
        ("ab2cd3ef", "AB2CD3EF"),
        ("abc_2", "ABC_2"),
        ("abc_2d", "ABC_2D"),
        ("abc_2d3", "ABC_2D3"),
        ("abc_2def", "ABC_2DEF"),
        ("abc_12", "ABC_12"),
        ("abc_123def", "ABC_123DEF"),
        ("something_2d", "SOMETHING_2D"),
        ("something_2abc", "SOMETHING_2ABC"),
        ("something_2dand", "SOMETHING_2DAND"),
        ("something_t0", "SOMETHING_T0"),
        ("something_t0and", "SOMETHING_T0AND"),
        ("abc_t0", "ABC_T0"),
        # From snake_case without dot delimiter
        ("abc_def", "ABC_DEF"),
        # From snake_case with dot delimiter
        ("abc.def", "ABC.DEF"),
        ("abc_def.xyz", "ABC_DEF.XYZ"),
        ("abc_def.uvw_xyz", "ABC_DEF.UVW_XYZ"),
    )
    pascal_to_upper_case_test_cases = (
        # From PascalCase with digits
        ("A2", "A2"),
        ("AB2", "AB2"),
        ("AB2D", "AB2D"),
        ("ABC2D", "ABC2D"),
        ("ABC2", "ABC2"),
        ("AB2CD3EF", "AB2CD3EF"),
        ("Abc2", "ABC_2"),
        ("Abc2D", "ABC_2D"),
        ("Abc2D3", "ABC_2D3"),
        ("Abc2DEF", "ABC_2DEF"),
        ("Abc12", "ABC_12"),
        ("Abc123DEF", "ABC_123DEF"),
        ("Something2D", "SOMETHING_2D"),
        ("Something2ABC", "SOMETHING_2ABC"),
        ("Something2DAND", "SOMETHING_2DAND"),
        ("SomethingT0", "SOMETHING_T0"),
        ("SomethingT0AND", "SOMETHING_T0AND"),
        ("AbcT0", "ABC_T0"),
        # From PascalCase without dot delimiter
        ("AbcDef", "ABC_DEF"),
        # From PascalCase with dot delimiter
        ("Abc.Def", "ABC.DEF"),
        ("AbcDef.Xyz", "ABC_DEF.XYZ"),
        ("AbcDef.UvwXyz", "ABC_DEF.UVW_XYZ"),
    )

    for pascal_case_value, snake_case_value in pascal_to_snake_case_test_cases:
        assert CaseUtil.pascal_to_snake_case(pascal_case_value) == snake_case_value
        assert CaseUtil.snake_to_pascal_case(snake_case_value) == pascal_case_value

    for snake_case_value, upper_case_value in snake_to_upper_case_test_cases:
        assert CaseUtil.snake_to_upper_case(snake_case_value) == upper_case_value
        assert CaseUtil.upper_to_snake_case(upper_case_value) == snake_case_value

    for pascal_case_value, upper_case_value in pascal_to_upper_case_test_cases:
        assert CaseUtil.pascal_to_upper_case(pascal_case_value) == upper_case_value
        assert CaseUtil.upper_to_pascal_case(upper_case_value) == pascal_case_value


def test_non_alphanumeric():
    """Test CaseUtil._check_non_alphanumeric."""

    # Underscore
    CaseUtil._check_non_alphanumeric("a_b", "sample_format", allow_underscore=True)  # Do not throw
    with pytest.raises(Exception):
        CaseUtil._check_non_alphanumeric("a_b", "sample_format")

    # Other characters
    with pytest.raises(Exception):
        CaseUtil._check_non_alphanumeric("abc\n", "sample_format")
    with pytest.raises(Exception):
        CaseUtil._check_non_alphanumeric("abc\rdef", "sample_format")
    with pytest.raises(Exception):
        CaseUtil._check_non_alphanumeric("\ufeffabc_def", "sample_format")


def test_any_to_snake_case():
    test_cases = (
        # Already valid snake_case
        ("abc_def", "abc_def"),
        ("abc_2d", "abc_2d"),
        # PascalCase
        ("AbcDef", "abc_def"),
        ("Abc2D", "abc_2d"),
        ("ABC2DEF", "abc2def"),
        # camelCase
        ("abcDef", "abc_def"),
        # UPPER_CASE
        ("ABC_DEF", "abc_def"),
        ("ABC_2D", "abc_2d"),
        # Title Case
        ("Abc Def", "abc_def"),
        # kebab-case
        ("abc-def", "abc_def"),
        # Mixed formats
        ("Some_MixedCase", "some_mixed_case"),
        ("UPPER_mixed_Case", "upper_mixed_case"),
        # Uppercase acronym runs
        ("getHTTPResponse", "get_http_response"),
        ("XMLParser", "xml_parser"),
        ("ABCDef", "abc_def"),
        # Invalid inputs (normalized via round-trip)
        ("abc_2d_ef", "abc_2def"),
        ("a_b_c", "abc"),
        ("ABC2Def", "abc2def"),
        # With dots
        ("AbcDef.UvwXyz", "abc_def.uvw_xyz"),
    )

    for input_value, expected in test_cases:
        result = CaseUtil.any_to_snake_case(input_value)
        assert result == expected, f"any_to_snake_case({input_value!r}) = {result!r}, expected {expected!r}"
        CaseUtil.check_snake_case(result)

    assert CaseUtil.any_to_snake_case(None) is None
    assert CaseUtil.any_to_snake_case("") == ""


def test_any_to_pascal_case():
    test_cases = (
        # Already valid PascalCase
        ("AbcDef", "AbcDef"),
        ("Abc2D", "Abc2D"),
        ("ABC2DEF", "ABC2DEF"),
        # snake_case
        ("abc_def", "AbcDef"),
        ("abc_2d", "Abc2D"),
        # camelCase
        ("abcDef", "AbcDef"),
        # UPPER_CASE
        ("ABC_DEF", "AbcDef"),
        ("ABC_2D", "Abc2D"),
        # Title Case
        ("Abc Def", "AbcDef"),
        # kebab-case
        ("abc-def", "AbcDef"),
        # Mixed formats
        ("Some_MixedCase", "SomeMixedCase"),
        # Uppercase acronym runs
        ("getHTTPResponse", "GetHttpResponse"),
        ("XMLParser", "XmlParser"),
        ("ABCDef", "AbcDef"),
        # Invalid inputs (normalized via round-trip)
        ("abc_2d_ef", "Abc2DEF"),
        ("ABC2Def", "ABC2DEF"),
        # With dots
        ("AbcDef.UvwXyz", "AbcDef.UvwXyz"),
        ("abc_def.uvw_xyz", "AbcDef.UvwXyz"),
    )

    for input_value, expected in test_cases:
        result = CaseUtil.any_to_pascal_case(input_value)
        assert result == expected, f"any_to_pascal_case({input_value!r}) = {result!r}, expected {expected!r}"
        CaseUtil.check_pascal_case(result)

    assert CaseUtil.any_to_pascal_case(None) is None
    assert CaseUtil.any_to_pascal_case("") == ""


if __name__ == "__main__":
    pytest.main([__file__])
