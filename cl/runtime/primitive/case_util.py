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
from cl.runtime.primitive.char_util import CharUtil

_ALPHANUMERIC_RE: Pattern = re.compile(r"[^a-zA-Z0-9 .]")
"""Match sequences where all characters are either letters or digits, also allowing dot and space."""

_ALPHANUMERIC_OR_UNDERSCORE_RE: Pattern = re.compile(r"[^a-zA-Z0-9 ._]")
"""Match sequences where all characters are either letters or digits or an underscore, also allowing dot and space."""

_PASCAL_TO_SNAKE_RE: Pattern = re.compile(r"([a-z])([A-Z\d])")
"""Insert underscore after a lowercase letter followed by an uppercase letter or digit."""

_DIGIT_UNDERSCORE_VIOLATIONS_RE: Pattern = re.compile(r"(?<=\d)_")
"""No underscore after a digit (digits glue forward onto following letters)."""

_DIGIT_WITHOUT_SPACE_RE: Pattern = re.compile(r"(?<! )\d")
"""Digit without space pattern"""


class CaseUtil:
    """Utilities for case conversion between PascalCase, snake_case, UPPER_CASE, and Title Case.

    Conversion Rules:

        PascalCase to snake_case (forward rule):
            Insert _ after every lowercase letter followed by an uppercase letter or digit,
            then lowercase the result. Regex: re.sub(r'([a-z])([A-Z\\d])', r'\\1_\\2', s).lower()

            Examples:
                AbcDef -> abc_def          (lowercase-uppercase boundary)
                Abc2D -> abc_2d            (lowercase-digit boundary)
                ABC2D -> abc2d             (no lowercase, no _ inserted)
                AbcT0 -> abc_t0            (lowercase-uppercase boundary)
                Abc123DEF -> abc_123def    (lowercase-digit boundary, digits glue forward)

        snake_case to PascalCase (reverse rule):
            Split by _ into segments, pascalize each segment:
            - If the segment contains any digit, uppercase all letters
            - Otherwise, capitalize the first letter only (standard capitalize)

            Examples:
                abc_def -> AbcDef          (no digits: capitalize)
                abc_2d -> Abc2D            (segment 2d has digit: all uppercase)
                abc2d -> ABC2D             (single segment has digit: all uppercase)
                abc_t0 -> AbcT0            (segment t0 has digit: all uppercase)
                abc_123def -> Abc123DEF    (segment 123def has digit: all uppercase)

        Digit separator rule (No digit_):
            Digits glue forward onto following letters. No underscore may appear
            immediately after a digit: 2d not 2_d, 2abc not 2_abc.

        UPPER_CASE is snake_case uppercased, so the same digit separator rule applies.

        Title Case uses spaces instead of underscores, with the same pascalization per word.

        Invalid PascalCase (rejected by check_pascal_case):
            A segment is a maximal substring where no lowercase letter is
            immediately followed by an uppercase letter or digit (i.e. the
            forward rule inserts no _ within it). Each segment must satisfy:
            - Segment without digits: only the first letter may be uppercase
            - Segment with digits: all letters must be uppercase

            Segment examples:
                AbcDef    = Abc | Def       (split at c->D, lowercase-uppercase)
                Abc2DEF   = Abc | 2DEF      (split at c->2, lowercase-digit)
                ABC2DEF   = ABC2DEF         (single segment, no lowercase-to-upper/digit)

            Invalid examples (-> shows round-trip result):
                ABC -> Abc               (one segment, no digits, multiple uppercase)
                ABCDef -> Abcdef          (one segment, no digits, multiple uppercase)
                ABC2Def -> ABC2DEF        (one segment, has digits, lowercase 'ef')
                A2a -> A2A               (one segment, has digits, lowercase 'a')

        Invalid snake_case (rejected by check_snake_case):
            A segment with both digits and letters must be the last segment
            within its dot-delimited token. The all-uppercase pascalization
            of such a segment merges with the following segment, losing the
            underscore boundary.

            Invalid examples (-> shows round-trip result):
                abc_2d_ef -> abc_2def     (digit segment '2d' merges with 'ef')
                abc_2d_3 -> abc_2d3       (digit segment '2d' merges with '3')
                another_valid_3dcase_2 -> another_valid_3dcase2
                    (digit segment '3dcase' merges with '2')

        Invalid UPPER_CASE (rejected by check_upper_case):
            Same rules as invalid snake_case applied to the lowercased value.
    """

    @classmethod
    def is_empty(cls, value: str | None) -> bool:
        """Returns true if the string is None or ''."""
        # We cannot reuse the method from StringUtil here to avoid a cyclic reference
        return value is None or value == ""

    @classmethod
    def pascal_to_snake_case(cls, value: str | None) -> str | None:
        """Convert PascalCase to snake_case using a custom rule for separators in front of digits."""
        if cls.is_empty(value):
            return value
        cls.check_pascal_case(value)
        return cls._pascal_to_snake_unchecked(value)

    @classmethod
    def upper_to_snake_case(cls, value: str | None) -> str | None:
        """Convert UPPER_CASE to snake_case using a custom rule for separators in front of digits."""
        if cls.is_empty(value):
            return value
        cls.check_upper_case(value)
        return value.lower()

    @classmethod
    def snake_to_upper_case(cls, value: str | None) -> str | None:
        """Convert snake_case to UPPER_CASE using a custom rule for separators in front of digits."""
        if cls.is_empty(value):
            return value
        cls.check_snake_case(value)
        return value.upper()

    @classmethod
    def snake_to_pascal_case(cls, value: str | None) -> str | None:
        """Convert snake_case to PascalCase using a custom rule for separators in front of digits."""
        if cls.is_empty(value):
            return value
        cls.check_snake_case(value)
        return cls._snake_to_pascal_unchecked(value)

    @classmethod
    def upper_to_pascal_case(cls, value: str | None) -> str | None:
        """Convert UPPER_CASE to PascalCase using a custom rule for separators in front of digits."""
        if cls.is_empty(value):
            return value
        cls.check_upper_case(value)
        return cls.snake_to_pascal_case(value.lower())

    @classmethod
    def pascal_to_upper_case(cls, value: str | None) -> str | None:
        """Convert PascalCase to UPPER_CASE using a custom rule for separators in front of digits."""
        if cls.is_empty(value):
            return value
        cls.check_pascal_case(value)
        snake_case_value = cls.pascal_to_snake_case(value)
        return snake_case_value.upper()

    @classmethod
    def pascal_to_title_case(cls, value: str | None) -> str | None:
        """Convert PascalCase to Title Case using a custom rule for separators in front of digits."""
        if cls.is_empty(value):
            return value
        cls.check_pascal_case(value)
        snake_case_value = cls.pascal_to_snake_case(value)

        # Apply the processing (i.e. `_pascalize_segment()`) function to each segment and join
        # them into Title Case.
        return " ".join(cls._pascalize_segment(segment) for segment in snake_case_value.split("_"))

    @classmethod
    def snake_to_title_case(cls, value: str | None) -> str | None:
        """Convert snake_case to Title Case using a custom rule for separators in front of digits."""
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
        cls._check_round_trip(value, "snake_case")

    @classmethod
    def check_pascal_case(cls, value: str | None) -> None:
        """Error message if arg is not PascalCase or does not follow the custom rule for separators in front of digits."""
        if cls.is_empty(value):
            # Consider None or empty string compliant with the format
            return
        cls._check_non_alphanumeric(value, "PascalCase", allow_underscore=False)
        cls._check_no_space(value, "PascalCase")
        cls._check_no_underscore(value, "PascalCase")
        cls._check_first_letter_capitalized(value, "PascalCase")
        cls._check_round_trip(value, "PascalCase")

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
        cls._check_round_trip(value, "UPPER_CASE")

    @classmethod
    def is_pascal_case(cls, value: str) -> bool:
        """Check if the string is in PascalCase."""
        try:
            cls.check_pascal_case(value)
            return True
        except RuntimeError:
            return False

    @classmethod
    def is_snake_case(cls, value: str) -> bool:
        """Check if the string is in snake_case."""
        try:
            cls.check_snake_case(value)
            return True
        except RuntimeError:
            return False

    @classmethod
    def is_title_case(cls, value: str) -> bool:
        """Check if the string is in Title Case."""
        try:
            cls.check_title_case(value)
            return True
        except RuntimeError:
            return False

    @classmethod
    def is_upper_case(cls, value: str) -> bool:
        """Check if the string is in UPPER_CASE."""
        try:
            cls.check_upper_case(value)
            return True
        except RuntimeError:
            return False

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
        # snake_case must have an underscore in front of digits
        # snake_case forbids underscore between digits
        if _DIGIT_UNDERSCORE_VIOLATIONS_RE.search(value):
            raise RuntimeError(
                f"String {value} is not snake_case because it does not follow the rule "
                f"for separators in front and between digits.",
            )

    @classmethod
    def _check_title_case_digit_separator(cls, value: str) -> None:
        """Error message stating string does not follow the custom rule for separators in front of digits"""
        # Title Case must have a space in front of digits
        if _DIGIT_WITHOUT_SPACE_RE.search(value):
            raise RuntimeError(
                f"String {value} is not Title Case because it does not follow the rule "
                f"for separators in front of digits.",
            )

    @classmethod
    def _check_round_trip(cls, value: str, format_: str) -> None:
        """Error message if the value does not survive a lossless round-trip conversion."""
        if format_ == "PascalCase":
            back = cls._snake_to_pascal_unchecked(cls._pascal_to_snake_unchecked(value))
        elif format_ == "snake_case":
            back = cls._pascal_to_snake_unchecked(cls._snake_to_pascal_unchecked(value))
        elif format_ == "UPPER_CASE":
            back = cls._pascal_to_snake_unchecked(cls._snake_to_pascal_unchecked(value.lower())).upper()
        else:
            return
        if back != value:
            raise RuntimeError(
                f"String {value} is not {format_} because it does not round-trip "
                f"losslessly (converts to {back}).",
            )

    @classmethod
    def _check_upper_case_digit_separator(cls, value: str) -> None:
        """Error message stating string does not follow the custom rule for digit separators"""
        # Make a round trip from snake_case to PascalCase and back to snake_case to check
        # if the value stays the same
        if _DIGIT_UNDERSCORE_VIOLATIONS_RE.search(value):
            raise RuntimeError(
                f"String {value} is not UPPER_CASE because it does not follow the rule "
                f"for separators in front and between digits.",
            )

    @classmethod
    def _pascal_to_snake_unchecked(cls, value: str) -> str:
        """Apply the forward rule without validation (used by round-trip checks)."""
        return _PASCAL_TO_SNAKE_RE.sub(r"\1_\2", value).lower()

    @classmethod
    def _snake_to_pascal_unchecked(cls, value: str) -> str:
        """Apply the reverse rule without validation (used by round-trip checks)."""
        return ".".join(
            "".join(cls._pascalize_segment(segment) for segment in token.split("_"))
            for token in value.split(".")
        )

    @classmethod
    def _pascalize_segment(cls, segment: str) -> str:
        """
        Pascalize a segment (substring between 2 underscores) from snake_case
        using a custom rule for separators in front of digits.

        If the segment contains any digit, all letters are uppercased.
        Otherwise, only the first letter is uppercased (standard capitalize).
        """
        if not segment:
            return segment
        if any(c.isdigit() for c in segment):
            return segment.upper()
        return segment.capitalize()
