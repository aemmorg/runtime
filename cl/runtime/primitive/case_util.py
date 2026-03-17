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
from typing import Pattern
from memoization import cached
from cl.runtime.primitive.char_util import CharUtil

_ALPHANUMERIC_RE: Pattern = re.compile(r"[^a-zA-Z0-9 .]")
"""Match sequences where all characters are either letters or digits, also allowing dot and space."""

_ALPHANUMERIC_OR_UNDERSCORE_RE: Pattern = re.compile(r"[^a-zA-Z0-9 ._]")
"""Match sequences where all characters are either letters or digits or an underscore, also allowing dot and space."""

_DIGIT_UNDERSCORE_VIOLATIONS_RE: Pattern = re.compile(r"(?<=\d)_(?=\d)|(?<![_\d])\d")
"""Digit without preceding underscore or underscore between digits pattern"""

_DIGIT_WITHOUT_SPACE_RE: Pattern = re.compile(r"(?<! )\d")
"""Digit without space pattern"""


class CaseUtil:
    """
    Utilities for case conversion between PascalCase, snake_case, UPPER_CASE, and Title Case.

    PascalCase to snake_case:
        Split at the boundary where a lowercase letter is followed by an uppercase letter
        or digit, concatenate with underscores, and lowercase everything.

        ``AbcDef``    -> ``abc_def``
        ``Abc2``      -> ``abc_2``
        ``Abc2DEF``   -> ``abc_2def``

    snake_case to PascalCase:
        Split on underscores. In segments containing digits, uppercase all letters.
        In other segments, capitalize the first letter. Concatenate without underscores.

        ``abc_def``   -> ``AbcDef``
        ``abc_2``     -> ``Abc2``
        ``abc_2def``  -> ``Abc2DEF``

    UPPER_CASE and Title Case conversions go through snake_case as an intermediate form.

    Both ``pascal_to_snake_case`` and ``snake_to_pascal_case`` verify the round-trip
    and raise an error if it does not match.
    """

    @classmethod
    def is_empty(cls, value: str | None) -> bool:
        """Returns true if the string is None or ''."""
        # We cannot reuse the method from StringUtil here to avoid a cyclic reference
        return value is None or value == ""

    @classmethod
    @cached
    def pascal_to_snake_case(cls, value: str | None) -> str | None:
        """Convert PascalCase to snake_case, error if round-trip does not match."""
        if cls.is_empty(value):
            return value
        cls.check_pascal_case(value)
        # Look up in CaseConversionRule first
        from cl.runtime.primitive.case_conversion_rule import CaseConversionRule
        rule_result = CaseConversionRule.get_snake_case(value)
        if rule_result is not None:
            return rule_result

        # Perform conversion, error if not a lossless roundtrip
        result = cls._pascal_to_snake_unchecked(value)
        # Verify round-trip
        back = cls._snake_to_pascal_unchecked(result)
        if back != value:
            raise RuntimeError(
                f"String '{value}' cannot be converted to snake_case because the round-trip conversion\n"
                f"produces '{back}' instead of the original '{value}'."
                f"Please either:\n"
                f"(a) Change PascalCase name from '{value}' to '{back}' to allow lossless\n"
                f"    PascalCase to snake_case roundtrip or\n"
                f"(b) Add the intended snake_case and PascalCase pair to CaseConversionRule.csv.\n"
            )
        return result

    @classmethod
    def upper_to_snake_case(cls, value: str | None) -> str | None:
        """Convert UPPER_CASE to snake_case by lowercasing."""
        if cls.is_empty(value):
            return value
        cls.check_upper_case(value)
        return value.lower()

    @classmethod
    def snake_to_upper_case(cls, value: str | None) -> str | None:
        """Convert snake_case to UPPER_CASE by uppercasing."""
        if cls.is_empty(value):
            return value
        cls.check_snake_case(value)
        return value.upper()

    @classmethod
    @cached
    def snake_to_pascal_case(cls, value: str | None) -> str | None:
        """Convert snake_case to PascalCase, error if round-trip does not match."""
        if cls.is_empty(value):
            return value
        cls.check_snake_case(value)
        # Look up in CaseConversionRule first
        from cl.runtime.primitive.case_conversion_rule import CaseConversionRule
        rule_result = CaseConversionRule.get_pascal_case(value)
        if rule_result is not None:
            return rule_result

        # Perform conversion, error if not a lossless roundtrip
        result = cls._snake_to_pascal_unchecked(value)
        # Verify round-trip
        back = cls._pascal_to_snake_unchecked(result)
        if back != value:
            raise RuntimeError(
                f"String '{value}' cannot be converted to PascalCase because the round-trip conversion\n"
                f"produces '{back}' instead of the original '{value}'."
                f"Please either:\n"
                f"(a) Change snake_case string from '{value}' to '{back}' to allow lossless\n"
                f"    snake_case to PascalCase roundtrip or\n"
                f"(b) Add the intended snake_case and PascalCase pair to CaseConversionRule.csv.\n"
            )
        return result

    @classmethod
    def upper_to_pascal_case(cls, value: str | None) -> str | None:
        """Convert UPPER_CASE to PascalCase. Convert to snake_case, then to PascalCase."""
        if cls.is_empty(value):
            return value
        cls.check_upper_case(value)
        return cls.snake_to_pascal_case(value.lower())

    @classmethod
    def pascal_to_upper_case(cls, value: str | None) -> str | None:
        """Convert PascalCase to UPPER_CASE. Convert to snake_case, then uppercase."""
        if cls.is_empty(value):
            return value
        cls.check_pascal_case(value)
        snake_case_value = cls.pascal_to_snake_case(value)
        return snake_case_value.upper()

    @classmethod
    def pascal_to_title_case(cls, value: str | None) -> str | None:
        """Convert PascalCase to Title Case. Convert to snake_case, then pascalize segments with spaces."""
        if cls.is_empty(value):
            return value
        cls.check_pascal_case(value)
        snake_case_value = cls.pascal_to_snake_case(value)

        return " ".join(cls.__pascalize_segment(segment) for segment in snake_case_value.split("_"))

    @classmethod
    def snake_to_title_case(cls, value: str | None) -> str | None:
        """Convert snake_case to Title Case. Convert to PascalCase, then to Title Case."""
        if cls.is_empty(value):
            return value
        cls.check_snake_case(value)
        pascal_case_value = cls.snake_to_pascal_case(value)
        return cls.pascal_to_title_case(pascal_case_value)

    @classmethod
    def snake_to_pascal_case_keep_trailing_underscore(cls, value: str | None):
        """
        Convert snake_case_ to PascalCase_ using a custom rule for separators in front of digits
        and keep ending underscore.
        """
        if cls.is_empty(value):
            return value

        return cls.snake_to_pascal_case(value.removesuffix("_")) + ("_" if value.endswith("_") else "")

    @classmethod
    def pascale_to_snake_case_keep_trailing_underscore(cls, value: str | None):
        """
        Convert PascalCase_ to snake_case_ using a custom rule for separators in front of digits
        and keep ending underscore.
        """
        if cls.is_empty(value):
            return value

        return cls.pascal_to_snake_case(value.removesuffix("_")) + ("_" if value.endswith("_") else "")

    @classmethod
    def check_snake_case(cls, value: str | None) -> None:
        """Error message if arg is not snake_case or does not follow the custom rule for separators in front of digits."""
        if cls.is_empty(value):
            # Consider None or empty string compliant with the format
            return
        cls._check_non_alphanumeric(value, "snake_case", allow_underscore=True)
        cls._check_no_space(value, "snake_case")
        cls._check_no_upper(value, "snake_case")
        cls._check_double_underscore(value, "snake_case")
        cls._check_snake_case_digit_separator(value)

    @classmethod
    def check_pascal_case(cls, value: str | None) -> None:
        """Error message if arg is not PascalCase."""
        if cls.is_empty(value):
            # Consider None or empty string compliant with the format
            return
        cls._check_non_alphanumeric(value, "PascalCase", allow_underscore=False)
        cls._check_no_space(value, "PascalCase")
        cls._check_no_underscore(value, "PascalCase")
        cls._check_first_letter_capitalized(value, "PascalCase")

    @classmethod
    def check_title_case(cls, value: str | None) -> None:
        """Error message if arg is not Title Case or does not follow the custom rule for separators in front of digits."""
        if cls.is_empty(value):
            # Consider None or empty string compliant with the format
            return
        cls._check_non_alphanumeric(value, "Title Case", allow_underscore=False)
        cls._check_no_underscore(value, "Title Case")
        cls._check_first_letter_capitalized(value, "Title Case")
        cls._check_title_case_digit_separator(value)

    @classmethod
    def check_upper_case(cls, value: str | None) -> None:
        """Error message if arg is not UPPER_CASE or does not follow the custom rule for separators in front of digits."""
        if cls.is_empty(value):
            # Consider None or empty string compliant with the format
            return
        cls._check_non_alphanumeric(value, "UPPER_CASE", allow_underscore=True)
        cls._check_no_space(value, "UPPER_CASE")
        cls._check_no_lower(value, "UPPER_CASE")
        cls._check_upper_case_digit_separator(value)

    @classmethod
    def is_pascal_case(cls, value: str) -> bool:
        """Check if the string is in PascalCase by basic format check."""
        if cls.is_empty(value):
            return True
        # Only alphanumeric and dots, no spaces or underscores, first letter capitalized
        if _ALPHANUMERIC_RE.search(value) or " " in value or "_" in value or not value[0].isupper():
            return False
        return True

    @classmethod
    def is_snake_case(cls, value: str) -> bool:
        """Check if the string is in snake_case by basic format check."""
        if cls.is_empty(value):
            return True
        # Only lowercase, digits, underscores, and dots, no spaces or uppercase, no double underscores
        if _ALPHANUMERIC_OR_UNDERSCORE_RE.search(value) or " " in value or any(c.isupper() for c in value) or "__" in value:
            return False
        return True

    @classmethod
    def is_title_case(cls, value: str) -> bool:
        """Check if the string is in Title Case by basic format check."""
        if cls.is_empty(value):
            return True
        # Only alphanumeric, dots, and spaces, no underscores, first letter capitalized
        if _ALPHANUMERIC_RE.search(value) or "_" in value or not value[0].isupper():
            return False
        return True

    @classmethod
    def is_upper_case(cls, value: str) -> bool:
        """Check if the string is in UPPER_CASE by basic format check."""
        if cls.is_empty(value):
            return True
        # Only uppercase, digits, underscores, and dots, no spaces or lowercase
        if _ALPHANUMERIC_OR_UNDERSCORE_RE.search(value) or " " in value or any(c.islower() for c in value):
            return False
        return True

    @classmethod
    def _check_non_alphanumeric(cls, value: str, format_: str, allow_underscore: bool) -> None:
        """Error message stating the string does not follow format because it contains non-alphanumeric characters."""
        if allow_underscore:
            non_alphanumeric = re.findall(_ALPHANUMERIC_OR_UNDERSCORE_RE, value)
        else:
            non_alphanumeric = list(set(re.findall(_ALPHANUMERIC_RE, value)))
        if non_alphanumeric:
            non_alphanumeric_names = ", ".join(CharUtil.describe_char(char) for char in non_alphanumeric)
            other_than_underscore_msg = " other than underscore" if allow_underscore else ""
            raise RuntimeError(
                f"String '{value}' is not '{format_}' because it contains "
                f"non-alphanumeric characters{other_than_underscore_msg}: "
                f"{non_alphanumeric_names}"
            )

    @classmethod
    def _check_no_space(cls, value: str, format_: str) -> None:
        """Error message stating string does not follow format if it contains a space."""
        if " " in value:
            raise RuntimeError(f"String {value} is not {format_} because it contains a space.")

    @classmethod
    def _check_no_underscore(cls, value: str, format_: str) -> None:
        """Error message stating string does not follow format if it contains an underscore."""
        if "_" in value:
            raise RuntimeError(f"String {value} is not {format_} because it contains an underscore.")

    @classmethod
    def _check_double_underscore(cls, value: str, format_: str) -> None:
        """Error message stating string does not follow format if it contains a double underscore."""
        if "__" in value:
            raise RuntimeError(f"String {value} is not {format_} because it contains a doubled underscore.")

    @classmethod
    def _check_no_lower(cls, value: str, format_: str) -> None:
        """Error message stating string does not follow format if it contains a lowercase character."""
        if any(char.islower() for char in value):
            raise RuntimeError(f"String {value} is not {format_} because it contains a lowercase character.")

    @classmethod
    def _check_no_upper(cls, value: str, format_: str) -> None:
        """Error message stating string does not follow format if it contains an uppercase character."""
        if any(char.isupper() for char in value):
            raise RuntimeError(f"String {value} is not {format_} because it contains an uppercase character.")

    @classmethod
    def _check_first_letter_capitalized(cls, value: str, format_: str) -> None:
        """Error message stating string does not follow format if it does not start with an uppercase letter."""
        if not value[0].isupper():
            raise RuntimeError(f"String {value} is not {format_} because the first letter is lowercase.")

    @classmethod
    def _check_snake_case_digit_separator(cls, value: str) -> None:
        """Error message stating string does not follow the custom rule for digit separators"""
        if _DIGIT_UNDERSCORE_VIOLATIONS_RE.search(value):
            raise RuntimeError(
                f"String {value} is not snake_case because it does not follow the rule "
                f"for separators in front and between digits.",
            )

    @classmethod
    def _check_title_case_digit_separator(cls, value: str) -> None:
        """Error message stating string does not follow the custom rule for separators in front of digits"""
        if _DIGIT_WITHOUT_SPACE_RE.search(value):
            raise RuntimeError(
                f"String {value} is not Title Case because it does not follow the rule "
                f"for separators in front of digits.",
            )

    @classmethod
    def _check_upper_case_digit_separator(cls, value: str) -> None:
        """Error message stating string does not follow the custom rule for digit separators"""
        if _DIGIT_UNDERSCORE_VIOLATIONS_RE.search(value):
            raise RuntimeError(
                f"String {value} is not UPPER_CASE because it does not follow the rule "
                f"for separators in front and between digits.",
            )

    @classmethod
    def _pascal_to_snake_unchecked(cls, value: str) -> str:
        """Convert PascalCase to snake_case without validation."""
        result = re.sub(r"([a-z])([A-Z0-9])", r"\1_\2", value)
        return result.lower()

    @classmethod
    def _snake_to_pascal_unchecked(cls, value: str) -> str:
        """Convert snake_case to PascalCase without validation."""
        input_tokens = value.split(".")
        return ".".join(
            ["".join(cls.__pascalize_segment(segment) for segment in token.split("_")) for token in input_tokens]
        )

    @classmethod
    def __pascalize_segment(cls, segment: str) -> str:
        """
        Pascalize a segment (substring between 2 underscores) from snake_case.
        If the segment contains any digit, all letters become uppercase.
        Otherwise, capitalize the first letter of the segment.
        """
        if any(char.isdigit() for char in segment):
            return segment.upper()
        return segment.capitalize()
