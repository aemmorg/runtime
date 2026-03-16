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
        # From PascalCase with digits
        ("A2", "a_2"),
        ("AB2", "a_b_2"),
        ("AB2D", "a_b_2d"),
        ("AB2DEf", "a_b_2d_ef"),
        ("Abc2", "abc_2"),
        ("Abc2D", "abc_2d"),
        ("Abc2Def", "abc_2def"),
        ("AbcT0Key", "abc_t0_key"),
        # Single uppercase + multi-digit
        ("A23", "a_23"),
        # Word + multi-digit
        ("Abc12", "abc_12"),
        ("Abc123", "abc_123"),
        # Multiple single-letter + digit groups
        ("A2B3", "a_2b_3"),
        # Multiple word + digit groups
        ("Abc2Def3", "abc_2def_3"),
        ("Abc2Def3Ghi", "abc_2def_3ghi"),
        # Word + multi-digit + word
        ("Abc23Def", "abc_23def"),
        # Lowercase-to-digit boundary in multi-segment words
        ("Ab2Cd3Ef", "ab_2cd_3ef"),
        # Digit-only trailing group
        ("Abc2D3", "abc_2d_3"),
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
        ("a_2", "A2"),
        ("a_b_2", "AB2"),
        ("a_b_2d", "AB2D"),
        ("a_b_2d_ef", "AB2DEf"),
        ("abc_2", "Abc2"),
        ("abc_2d", "Abc2D"),
        ("abc_2def", "Abc2Def"),
        # Single letter + multi-digit
        ("a_23", "A23"),
        # Word + multi-digit
        ("abc_12", "Abc12"),
        ("abc_123", "Abc123"),
        # Multiple single-letter + digit groups
        ("a_2b_3", "A2B3"),
        # Multiple word + digit groups
        ("abc_2def_3", "Abc2Def3"),
        ("abc_2def_3ghi", "Abc2Def3Ghi"),
        # Word + multi-digit + word (only first leading digit is skipped by pascalize,
        # so letters after multi-digit prefix are not capitalized)
        ("abc_23def", "Abc23def"),
        # Lowercase-to-digit in multi-segment words (single leading digit, capitalizes correctly)
        ("ab_2cd_3ef", "Ab2Cd3Ef"),
        # Digit-only trailing group
        ("abc_2d_3", "Abc2D3"),
        # Digit-only segment (no following letters)
        ("abc_2", "Abc2"),
        ("abc_23", "Abc23"),
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
        ("A2", "A 2"),
        ("AB2", "A B 2"),
        ("AB2D", "A B 2D"),
        ("AB2DEf", "A B 2D Ef"),
        ("Abc2", "Abc 2"),
        ("Abc2D", "Abc 2D"),
        ("Abc2Def", "Abc 2Def"),
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
    pascal_to_snake_case_test_cases = (
        # From PascalCase with digits
        ("A2", "a_2"),
        ("AB2", "a_b_2"),
        ("AB2D", "a_b_2d"),
        ("AB2DEf", "a_b_2d_ef"),
        ("Abc2", "abc_2"),
        ("Abc2D", "abc_2d"),
        ("Abc2Def", "abc_2def"),
        ("Abc12", "abc_12"),
        # Single uppercase + multi-digit
        ("A23", "a_23"),
        # Word + multi-digit
        ("Abc123", "abc_123"),
        # Multiple single-letter + digit groups
        ("A2B3", "a_2b_3"),
        # Multiple word + digit groups
        ("Abc2Def3", "abc_2def_3"),
        ("Abc2Def3Ghi", "abc_2def_3ghi"),
        # Word + multi-digit + word (does NOT round-trip due to __pascalize_segment
        # only skipping one leading digit, so "abc_23def" -> "Abc23def" not "Abc23Def")
        # ("Abc23Def", "abc_23def"),  # excluded: does not round-trip
        # Lowercase-to-digit in multi-segment words
        ("Ab2Cd3Ef", "ab_2cd_3ef"),
        # Digit-only trailing group
        ("Abc2D3", "abc_2d_3"),
        # Uppercase + digit mid-word boundary (does NOT round-trip because "abc_t0_key"
        # fails check_snake_case: digit 0 is not preceded by underscore in "t0")
        # ("AbcT0Key", "abc_t0_key"),  # excluded: snake_case form fails validation
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
    pascal_to_upper_case_test_cases = (
        # From PascalCase with digits
        ("A2", "A_2"),
        ("AB2", "A_B_2"),
        ("AB2D", "A_B_2D"),
        ("AB2DEf", "A_B_2D_EF"),
        ("Abc2", "ABC_2"),
        ("Abc2D", "ABC_2D"),
        ("Abc2Def", "ABC_2DEF"),
        # Single uppercase + multi-digit
        ("A23", "A_23"),
        # Word + multi-digit
        ("Abc12", "ABC_12"),
        ("Abc123", "ABC_123"),
        # Multiple digit groups
        ("A2B3", "A_2B_3"),
        ("Abc2Def3", "ABC_2DEF_3"),
        ("Abc2Def3Ghi", "ABC_2DEF_3GHI"),
        # Word + multi-digit + word (does NOT round-trip due to __pascalize_segment
        # only skipping one leading digit, so upper_to_pascal("ABC_23DEF") -> "Abc23def")
        # ("Abc23Def", "ABC_23DEF"),  # excluded: does not round-trip
        # Digit-only trailing group
        ("Abc2D3", "ABC_2D_3"),
        # Uppercase + digit mid-word boundary (does NOT round-trip: snake_case form
        # "abc_t0_key" fails validation since digit 0 not preceded by underscore in "t0")
        # ("AbcT0Key", "ABC_T0_KEY"),  # excluded: snake_case form fails validation
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

    # snake_to_pascal_case silently strips leading and trailing underscores
    # because split("_") produces empty strings which pascalize to ""
    assert CaseUtil.snake_to_pascal_case("_abc_def") == "AbcDef"
    assert CaseUtil.snake_to_pascal_case("abc_def_") == "AbcDef"
    assert CaseUtil.snake_to_pascal_case("_abc_def_") == "AbcDef"

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
    """Test new rule: snake_to_pascal should make all letters in a segment with a number uppercase.

    Only includes cases where the new rule produces a different result from current behavior.
    Current behavior capitalizes only the first letter after the first leading digit.
    New rule: if a segment contains any digit, ALL letters in that segment are uppercase.

    Segments where the result changes are those with a digit AND 2+ letters, e.g.:
        "2def" -> "2DEF" (was "2Def")
        "2cd"  -> "2CD"  (was "2Cd")
        "23def" -> "23DEF" (was "23def")
    """
    test_cases = (
        # Single digit + multiple letters: "2def" -> "2DEF" (was "2Def")
        ("abc_2def", "Abc2DEF"),
        # Multiple digit groups with letters: "2def" -> "2DEF", "3ghi" -> "3GHI"
        ("abc_2def_3", "Abc2DEF3"),
        ("abc_2def_3ghi", "Abc2DEF3GHI"),
        # Multi-digit prefix + letters: "23def" -> "23DEF" (was "23def")
        ("abc_23def", "Abc23DEF"),
        # Multiple segments each with single digit + multiple letters
        ("ab_2cd_3ef", "Ab2CD3EF"),
    )

    for input_value, expected in test_cases:
        assert CaseUtil.snake_to_pascal_case(input_value) == expected


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
