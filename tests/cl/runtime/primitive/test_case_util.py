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
    # Round-trippable cases (canonical PascalCase forms)
    test_cases = (
        # All-uppercase/digit segments (no lowercase -> no split points within)
        ("A2", "a2"),
        ("AB2", "ab2"),
        ("AB2D", "ab2d"),
        ("AB2DEF", "ab2def"),
        ("A23", "a23"),
        ("A2B3", "a2b3"),
        # Word + digit boundary
        ("Abc2", "abc_2"),
        ("Abc2D", "abc_2d"),
        ("Abc2DEF", "abc_2def"),
        ("Abc12", "abc_12"),
        ("Abc123", "abc_123"),
        ("Abc2DEF3", "abc_2def3"),
        ("Abc2DEF3GHI", "abc_2def3ghi"),
        ("Abc23DEF", "abc_23def"),
        ("Ab2CD3EF", "ab_2cd3ef"),
        ("Abc2D3", "abc_2d3"),
        # Without digits
        ("AbcDef", "abc_def"),
        # With dot delimiter
        ("Abc.Def", "abc.def"),
        ("AbcDef.Xyz", "abc_def.xyz"),
        ("AbcDef.UvwXyz", "abc_def.uvw_xyz"),
    )

    for input_value, expected in test_cases:
        assert CaseUtil.pascal_to_snake_case(input_value) == expected

    # Non-canonical PascalCase forms that fail round-trip
    non_roundtrip_cases = ("AB2DEf", "Abc2Def", "AbcT0Key", "Abc2Def3", "Abc2Def3Ghi", "Ab2Cd3Ef")
    for input_value in non_roundtrip_cases:
        with pytest.raises(RuntimeError, match="round-trip"):
            CaseUtil.pascal_to_snake_case(input_value)


def test_snake_to_pascal_case():
    # Round-trippable cases
    test_cases = (
        # Word + digit segments
        ("abc_2", "Abc2"),
        ("abc_2d", "Abc2D"),
        ("abc_2def", "Abc2DEF"),
        ("abc_12", "Abc12"),
        ("abc_123", "Abc123"),
        ("abc_23", "Abc23"),
        ("abc_23def", "Abc23DEF"),
        # Without digits
        ("abc_def", "AbcDef"),
        ("node_id", "NodeId"),
        # With dot delimiter
        ("abc.def", "Abc.Def"),
        ("abc_def.xyz", "AbcDef.Xyz"),
        ("abc_def.uvw_xyz", "AbcDef.UvwXyz"),
    )

    for input_value, expected in test_cases:
        assert CaseUtil.snake_to_pascal_case(input_value) == expected

    # snake_case forms that don't round-trip (pascal form converts back to different snake)
    non_roundtrip_cases = (
        "a_2", "a_b_2", "a_b_2d", "a_b_2d_ef", "a_23", "a_2b_3",
        "abc_2def_3", "abc_2def_3ghi", "ab_2cd_3ef", "abc_2d_3",
    )
    for input_value in non_roundtrip_cases:
        with pytest.raises(RuntimeError, match="round-trip"):
            CaseUtil.snake_to_pascal_case(input_value)


def test_pascal_to_title_case():
    test_cases = (
        ("A2", "A2"),
        ("AB2", "AB2"),
        ("AB2D", "AB2D"),
        ("AB2DEF", "AB2DEF"),
        ("Abc2", "Abc 2"),
        ("Abc2D", "Abc 2D"),
        ("Abc2DEF", "Abc 2DEF"),
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
    CaseUtil.check_snake_case("another_valid_3d_case_2")
    CaseUtil.check_snake_case("another_valid_case_2026")

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
        "invalid_snake_case2",
        "String invalid_snake_case2 is not snake_case because it does not follow the rule "
        "for separators in front and between digits.",
    )
    check_raises_error(
        CaseUtil.check_snake_case,
        "invalid_snake_case_1_2",
        "String invalid_snake_case_1_2 is not snake_case because it does not follow the rule "
        "for separators in front and between digits.",
    )


def test_check_pascal_case():
    # Valid cases
    CaseUtil.check_pascal_case("ValidPascalCase")
    CaseUtil.check_pascal_case("AnotherValidPascalCase")
    CaseUtil.check_pascal_case("AnotherValidPascalCaseWithDigits2")

    # Invalid cases
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
    CaseUtil.check_upper_case("UPPER_CASE_3D_EXAMPLE_2")
    CaseUtil.check_upper_case("UPPER_CASE_3D_EXAMPLE_23")

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
        "UPPER_CASE2",
        "String UPPER_CASE2 is not UPPER_CASE because it does not follow the rule "
        "for separators in front and between digits.",
    )
    check_raises_error(
        CaseUtil.check_upper_case,
        "UPPER_CASE_2_3",
        "String UPPER_CASE_2_3 is not UPPER_CASE because it does not follow the rule "
        "for separators in front and between digits.",
    )


def test_round_trip_conversions():
    # Only cases where the snake_case form passes check_snake_case validation
    # (digit preceded by underscore, no underscore between digits) can round-trip.
    # Cases like "A2" -> "a2" are excluded because "a2" fails check_snake_case.
    pascal_to_snake_case_test_cases = (
        # From PascalCase with digits
        ("Abc2", "abc_2"),
        ("Abc2D", "abc_2d"),
        ("Abc2DEF", "abc_2def"),
        # Word + multi-digit
        ("Abc12", "abc_12"),
        ("Abc123", "abc_123"),
        # Word + multi-digit + word
        ("Abc23DEF", "abc_23def"),
        # From PascalCase without dot delimiter
        ("AbcDef", "abc_def"),
        # From PascalCase with dot delimiter
        ("Abc.Def", "abc.def"),
        ("AbcDef.Xyz", "abc_def.xyz"),
        ("AbcDef.UvwXyz", "abc_def.uvw_xyz"),
    )
    snake_to_upper_case_test_cases = (
        # From snake_case with digits
        ("a_2", "A_2"),
        ("a_b_2", "A_B_2"),
        ("a_b_2d", "A_B_2D"),
        ("a_b_2d_ef", "A_B_2D_EF"),
        ("abc_2", "ABC_2"),
        ("abc_2d", "ABC_2D"),
        ("abc_2def", "ABC_2DEF"),
        # Single letter + multi-digit
        ("a_23", "A_23"),
        # Word + multi-digit
        ("abc_12", "ABC_12"),
        ("abc_123", "ABC_123"),
        # Multiple digit groups
        ("a_2b_3", "A_2B_3"),
        ("abc_2def_3", "ABC_2DEF_3"),
        ("abc_2def_3ghi", "ABC_2DEF_3GHI"),
        # Word + multi-digit + word
        ("abc_23def", "ABC_23DEF"),
        # Digit-only trailing group
        ("abc_2d_3", "ABC_2D_3"),
        # From snake_case without dot delimiter
        ("abc_def", "ABC_DEF"),
        # From snake_case with dot delimiter
        ("abc.def", "ABC.DEF"),
        ("abc_def.xyz", "ABC_DEF.XYZ"),
        ("abc_def.uvw_xyz", "ABC_DEF.UVW_XYZ"),
    )
    # Only cases where the snake_case form passes check_snake_case validation can round-trip.
    pascal_to_upper_case_test_cases = (
        # From PascalCase with digits
        ("Abc2", "ABC_2"),
        ("Abc2D", "ABC_2D"),
        ("Abc2DEF", "ABC_2DEF"),
        # Word + multi-digit
        ("Abc12", "ABC_12"),
        ("Abc123", "ABC_123"),
        # Word + multi-digit + word
        ("Abc23DEF", "ABC_23DEF"),
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


def test_leading_trailing_underscores():
    """Test current behavior of CaseUtil with leading and trailing underscores."""

    # check_snake_case accepts single leading or trailing underscore
    CaseUtil.check_snake_case("_abc")
    CaseUtil.check_snake_case("abc_")
    CaseUtil.check_snake_case("_abc_")
    CaseUtil.check_snake_case("_abc_def")
    CaseUtil.check_snake_case("abc_def_")

    # check_snake_case rejects double leading or trailing underscore
    with pytest.raises(RuntimeError, match="doubled underscore"):
        CaseUtil.check_snake_case("__abc")
    with pytest.raises(RuntimeError, match="doubled underscore"):
        CaseUtil.check_snake_case("abc__")

    # check_pascal_case rejects any underscore
    with pytest.raises(RuntimeError, match="non-alphanumeric"):
        CaseUtil.check_pascal_case("_AbcDef")
    with pytest.raises(RuntimeError, match="non-alphanumeric"):
        CaseUtil.check_pascal_case("AbcDef_")

    # snake_to_pascal_case with leading/trailing underscores fails round-trip
    with pytest.raises(RuntimeError, match="round-trip"):
        CaseUtil.snake_to_pascal_case("_abc_def")
    with pytest.raises(RuntimeError, match="round-trip"):
        CaseUtil.snake_to_pascal_case("abc_def_")
    with pytest.raises(RuntimeError, match="round-trip"):
        CaseUtil.snake_to_pascal_case("_abc_def_")

    # pascal_to_snake_case rejects underscores (PascalCase validation)
    with pytest.raises(RuntimeError, match="non-alphanumeric"):
        CaseUtil.pascal_to_snake_case("_AbcDef")
    with pytest.raises(RuntimeError, match="non-alphanumeric"):
        CaseUtil.pascal_to_snake_case("AbcDef_")

    # keep_trailing_underscore variants
    assert CaseUtil.snake_to_pascal_case_keep_trailing_underscore("abc_def_") == "AbcDef_"
    assert CaseUtil.snake_to_pascal_case_keep_trailing_underscore("abc_def") == "AbcDef"
    assert CaseUtil.pascale_to_snake_case_keep_trailing_underscore("AbcDef_") == "abc_def_"
    assert CaseUtil.pascale_to_snake_case_keep_trailing_underscore("AbcDef") == "abc_def"


def test_snake_to_pascal_case_digit_segment_uppercase():
    """Test that snake_to_pascal uppercases all letters in segments containing digits."""
    # Round-trippable cases
    test_cases = (
        ("abc_2def", "Abc2DEF"),
        ("abc_23def", "Abc23DEF"),
    )

    for input_value, expected in test_cases:
        assert CaseUtil.snake_to_pascal_case(input_value) == expected

    # Non-round-trippable cases (multiple digit segments separated by underscores)
    non_roundtrip_cases = ("abc_2def_3", "abc_2def_3ghi", "ab_2cd_3ef")
    for input_value in non_roundtrip_cases:
        with pytest.raises(RuntimeError, match="round-trip"):
            CaseUtil.snake_to_pascal_case(input_value)


def test_case_conversion():
    """Test that non-roundtrip conversions raise errors with informative messages."""

    # PascalCase to snake_case: Stub2Bar -> stub_2bar -> Stub2BAR != Stub2Bar
    with pytest.raises(RuntimeError, match="round-trip") as exc_info:
        CaseUtil.pascal_to_snake_case("Stub2Bar")
    msg = str(exc_info.value)
    assert "Stub2Bar" in msg
    assert "Stub2BAR" in msg
    assert "Change PascalCase name" in msg
    assert "CaseConversionRule.csv" in msg

    # snake_case to PascalCase: stub_b_2 -> StubB2 -> stub_b2 != stub_b_2
    with pytest.raises(RuntimeError, match="round-trip") as exc_info:
        CaseUtil.snake_to_pascal_case("stub_b_2")
    msg = str(exc_info.value)
    assert "stub_b_2" in msg
    assert "stub_b2" in msg
    assert "Change snake_case" in msg
    assert "CaseConversionRule.csv" in msg


def test_case_conversion_rule():
    """Test that CaseConversionRule.csv overrides algorithmic conversion."""

    # Plain entries (no leading/trailing underscores) - would fail roundtrip without CSV
    assert CaseUtil.snake_to_pascal_case("stub_2def") == "Stub2Def"
    assert CaseUtil.pascal_to_snake_case("Stub2Def") == "stub_2def"
    assert CaseUtil.snake_to_pascal_case("stub_2xyz") == "Stub2Xyz"
    assert CaseUtil.pascal_to_snake_case("Stub2Xyz") == "stub_2xyz"

    # Leading underscore entry
    assert CaseUtil.snake_to_pascal_case("_stub_2jkl") == "Stub2Jkl"
    assert CaseUtil.pascal_to_snake_case("Stub2Jkl") == "_stub_2jkl"

    # Trailing underscore entry
    assert CaseUtil.snake_to_pascal_case("stub_2mno_") == "Stub2Mno"
    assert CaseUtil.pascal_to_snake_case("Stub2Mno") == "stub_2mno_"

    # Both leading and trailing underscore entry
    assert CaseUtil.snake_to_pascal_case("_stub_2pqr_") == "Stub2Pqr"
    assert CaseUtil.pascal_to_snake_case("Stub2Pqr") == "_stub_2pqr_"


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


if __name__ == "__main__":
    pytest.main([__file__])
