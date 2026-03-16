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

_ALL_CAP_RE: Pattern = re.compile(r"([a-z])([A-Z])")
"""Match sequences where a lowercase letter ([a-z]) is immediately followed by an uppercase letter ([A-Z])"""

_LOWER_TO_DIGIT_RE: Pattern = re.compile(r"([a-z])(\d)")
"""Pattern to add underscores between lowercase letter and digit (e.g., "Abc2" -> "Abc_2")."""

_UPPER_DIGIT_TO_WORD_RE: Pattern = re.compile(r"([A-Z]\d+)([A-Z][a-z])")
"""Pattern to add underscores between uppercase+digit(s) and a new word (e.g., "T0Key" -> "T0_Key")."""

_UPPER_TO_DIGIT_RE: Pattern = re.compile(r"([A-Z])(\d+)(?=[^_\d]|$)")
"""Pattern to add underscores between uppercase letter and digit(s) not already handled (e.g., "B2" -> "B_2")."""

_CONSECUTIVE_CAP_RE: Pattern = re.compile(r"([A-Z])([A-Z])")
"""This pattern looks for uppercase sequences and adds an underscore between them if needed"""

_DIGIT_UNDERSCORE_VIOLATIONS_RE: Pattern = re.compile(r"(?<=\d)_(?=\d)|(?<![_\d])\d")
"""Digit without preceding underscore or underscore between digits pattern"""

_DIGIT_UPPER_NORMALIZE_RE: Pattern = re.compile(r"(\d)([A-Z]+)(?=[A-Z][a-z]|\d|$)")
"""Normalize new-format digit segments by lowercasing uppercase letters following a digit (e.g., "2DEF" -> "2def")."""

_DIGIT_WITHOUT_SPACE_RE: Pattern = re.compile(r"(?<! )\d")
"""Digit without space pattern"""


class CaseUtil:
    """
    Utilities for case conversion and other operations on string.

    This class converts between PascalCase, snake_case, UPPER_CASE, and Title Case
    using a custom rule for digit separators that ensures lossless round-trip conversion.

    Digit separator rules:
        - In snake_case and UPPER_CASE, every group of digits must be preceded by an underscore.
          For example, ``case2`` is invalid and must be written as ``case_2``.
        - No underscore is allowed between consecutive digits. For example, ``case_1_2`` is
          invalid and must be written as ``case_12``.

    PascalCase to snake_case digit behavior:
        - A lowercase-to-digit boundary inserts an underscore: ``Abc2`` -> ``abc_2``
        - An uppercase-to-digit boundary inserts an underscore: ``AB2`` -> ``a_b_2``
        - Multi-digit sequences stay together: ``Abc12`` -> ``abc_12``
        - Digits followed by lowercase letters form a single snake_case segment, so the
          underscore is placed before the digit group, not between the digits and the
          letters that follow: ``Abc2Def`` -> ``abc_2def`` (not ``abc_2_def``)
        - An uppercase letter followed by digits followed by a new word
          (uppercase + lowercase) inserts an underscore after the digit group:
          ``AbcT0Key`` -> ``abc_t0_key``

    snake_case to PascalCase digit behavior:
        - Each underscore-delimited segment is pascalized independently.
        - A digit-leading segment keeps its leading digits and capitalizes the remaining
          letters: ``2def`` -> ``2Def``, ``2d`` -> ``2D``, ``2`` -> ``2``
        - A letter-leading segment capitalizes its first letter: ``abc`` -> ``Abc``

    Round-trip examples (PascalCase <-> snake_case):
        ``A2``        <-> ``a_2``          Single uppercase + single digit
        ``A23``       <-> ``a_23``         Single uppercase + multi-digit
        ``Abc2``      <-> ``abc_2``        Word + single digit
        ``Abc12``     <-> ``abc_12``       Word + multi-digit
        ``Abc2D``     <-> ``abc_2d``       Word + digit + single uppercase
        ``Abc2Def``   <-> ``abc_2def``     Word + digit group with following letters
        ``A2B3``      <-> ``a_2b_3``       Multiple single-letter + digit groups
        ``Abc2Def3``  <-> ``abc_2def_3``   Multiple word + digit groups

    Known one-directional cases (PascalCase -> snake_case only, no round-trip):
        ``AbcT0Key``  -> ``abc_t0_key``    Uppercase + digit mid-word: the resulting
            snake_case ``t0`` has a digit not preceded by underscore, which fails
            check_snake_case validation, so the reverse conversion is not possible.
        ``Abc23Def``  -> ``abc_23def``     Multi-digit + word: __pascalize_segment
            only skips one leading digit, so ``abc_23def`` -> ``Abc23def`` (lowercase
            ``d``) rather than ``Abc23Def``.
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
        # Normalize digit segments: lowercase uppercase letters that follow a digit and belong
        # to the same segment (e.g., "Abc2DEF" -> "Abc2def") so the pipeline below handles them
        result = _DIGIT_UPPER_NORMALIZE_RE.sub(lambda m: m.group(1) + m.group(2).lower(), value)
        # Add underscores between consecutive uppercase letters
        result = _CONSECUTIVE_CAP_RE.sub(r"\1_\2", result)
        # Handle lowercase to uppercase transitions
        result = _ALL_CAP_RE.sub(r"\1_\2", result)
        # Insert underscore between lowercase letter and digit
        result = _LOWER_TO_DIGIT_RE.sub(r"\1_\2", result)
        # Insert underscore between uppercase+digit(s) and a new word (e.g., T0Key -> T0_Key)
        result = _UPPER_DIGIT_TO_WORD_RE.sub(r"\1_\2", result)
        # Insert underscore between uppercase letter and digit(s) in remaining cases
        result = _UPPER_TO_DIGIT_RE.sub(r"\1_\2", result)

        # Convert the final result to lowercase
        return result.lower()

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
        input_tokens = value.split(".")

        # Apply the processing (i.e. `__pascalize_segment()`) function to each segment and join
        # them into PascalCase.
        # Finally, join the tokens with dots and return the result
        return ".".join(
            ["".join(cls.__pascalize_segment(segment) for segment in token.split("_")) for token in input_tokens]
        )

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

        # Apply the processing (i.e. `__pascalize_segment()`) function to each segment and join
        # them into Title Case.
        return " ".join(cls.__pascalize_segment(segment) for segment in snake_case_value.split("_"))

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
        # NOTE: PascalCase shouldn't be checked for custom rule for separators in
        # front of digits, because there's no separators

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
    def __pascalize_segment(cls, segment: str) -> str:
        """
        Pascalize a segment (substring between 2 underscores) from snake_case
        using a custom rule for separators in front of digits.
        """
        # If the segment contains any digit, all letters become uppercase
        if any(char.isdigit() for char in segment):
            return segment.upper()
        # Otherwise, capitalize the first letter of the segment
        return segment.capitalize()
