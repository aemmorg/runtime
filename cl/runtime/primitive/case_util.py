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

_UPPER_RUN_BOUNDARY_RE: Pattern = re.compile(r"([A-Z]+)([A-Z][a-z])")
"""Split uppercase runs before an uppercase+lowercase pair (e.g., HTTPResponse -> HTTP_Response)."""

_ALPHA_UPPER_RUN_BOUNDARY_RE: Pattern = re.compile(r"(?<!\d)([A-Z]+)([A-Z][a-z])")
"""Like _UPPER_RUN_BOUNDARY_RE but skips runs preceded by a digit, preserving digit segment merging."""

_NON_ALNUM_DOT_RE: Pattern = re.compile(r"[^a-zA-Z0-9.]")
"""Match any character that is not alphanumeric or dot."""

_MULTI_UNDERSCORE_RE: Pattern = re.compile(r"_+")
"""Match one or more consecutive underscores."""

_SNAKE_TO_PASCAL_DICT: dict[str, str] = {"type_": "Type"}
"""Mapping from snake_case to PascalCase, initialized with hardcoded entries and expanded from settings on demand."""

_PASCAL_TO_SNAKE_DICT: dict[str, str] = {v: k for k, v in _SNAKE_TO_PASCAL_DICT.items()}
"""Mapping from PascalCase to snake_case, initialized with hardcoded entries and expanded from settings on demand."""

_CONVERSION_RULES_LOADED: bool = False
"""Flag indicating whether case conversion rules have been loaded from CaseSettings."""


class CaseUtil:
    """Utilities for case conversion between PascalCase, snake_case, UPPER_CASE, and Title Case.

    Conversion Rules:

        PascalCase to snake_case (forward rule):
            Two regex passes, then lowercase:
            1. Split uppercase runs before an uppercase+lowercase pair.
               Regex: re.sub(r'([A-Z]+)([A-Z][a-z])', r'\\1_\\2', s)
               This handles single-letter words: XLabel -> X_Label.
            2. Insert _ after every lowercase letter followed by an uppercase letter or digit.
               Regex: re.sub(r'([a-z])([A-Z\\d])', r'\\1_\\2', s)
            3. Lowercase the result

    Examples:
                AbcDef -> abc_def          (lowercase-uppercase boundary)
                Abc2D -> abc_2d            (lowercase-digit boundary)
                ABC2D -> abc2d             (no lowercase, no _ inserted)
                AbcT0 -> abc_t0            (lowercase-uppercase boundary)
                Abc123DEF -> abc_123def    (lowercase-digit boundary, digits glue forward)
                XLabel -> x_label          (uppercase-run split: X | Label)

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
                x_label -> XLabel          (single-letter segment: capitalize)

        Uppercase-run boundary rule:
            A run of consecutive uppercase letters followed by an uppercase+lowercase
            pair represents a word boundary before the last uppercase letter of the
            run, provided the run is not preceded by a digit. This allows single-letter
            words to round-trip losslessly: x_label -> XLabel -> x_label. Without
            this rule, the back-conversion would produce xlabel (no lowercase-uppercase
            boundary after X). The digit lookbehind ensures that digit segments
            (which are all-uppercase) still merge with following segments as required
            by the digit separator rule: abc_2d_ef remains invalid because the
            uppercase run in Abc2DEf is preceded by digit 2.

        Digit separator rule (No digit_):
            Digits glue forward onto following letters. No underscore may appear
            immediately after a digit: 2d not 2_d, 2abc not 2_abc.

        UPPER_CASE is snake_case uppercased, so the same digit separator rule applies.

        Title Case uses spaces instead of underscores, with the same pascalization per word.

        Valid PascalCase (accepted by check_pascal_case):
            A PascalCase string is valid if and only if it is the output of the
            snake_case to PascalCase conversion for some valid snake_case input.
            This is enforced by the round-trip check: pascal -> snake -> pascal
            must reproduce the original. Any PascalCase not generated by this
            algorithm is rejected.

            Examples of valid PascalCase (generated from snake_case):
                AbcDef    (from abc_def)
                Abc2DEF   (from abc_2def)
                XLabel    (from x_label, uppercase-run boundary split)
                YLim      (from y_lim)

            Examples of invalid PascalCase (not generated by the algorithm):
                ABCDef    (round-trips to AbcDef)
                ABC2Def   (round-trips to ABC2DEF)
                A2a       (round-trips to A2A)

        Invalid snake_case (rejected by check_snake_case):
            A segment with both digits and letters must be the last segment
            The all-uppercase pascalization of such a segment merges with
            the following segment, losing the underscore boundary.

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

        if value in _PASCAL_TO_SNAKE_DICT:
            return _PASCAL_TO_SNAKE_DICT[value]

        result = cls._pascal_to_snake_unchecked(value)
        back = cls._snake_to_pascal_unchecked(result)
        if back != value:
            cls._ensure_conversion_rules_loaded()
            if value in _PASCAL_TO_SNAKE_DICT:
                return _PASCAL_TO_SNAKE_DICT[value]
            raise RuntimeError(
                f"String '{value}' cannot be converted to snake_case because the round-trip conversion\n"
                f"produces '{back}' instead of the original '{value}'.\n"
                f"To resolve, either:\n"
                f"(a) Change PascalCase name from '{value}' to '{back}' to allow lossless\n"
                f"    PascalCase to snake_case roundtrip or\n"
                f"(b) Add the intended snake_case and PascalCase pair to case_conversion_rules in settings.\n"
            )
        return result

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

        if value in _SNAKE_TO_PASCAL_DICT:
            return _SNAKE_TO_PASCAL_DICT[value]

        result = cls._snake_to_pascal_unchecked(value)
        back = cls._pascal_to_snake_unchecked(result)
        if back != value:
            cls._ensure_conversion_rules_loaded()
            if value in _SNAKE_TO_PASCAL_DICT:
                return _SNAKE_TO_PASCAL_DICT[value]
            raise RuntimeError(
                f"String '{value}' cannot be converted to PascalCase because the round-trip conversion\n"
                f"produces '{back}' instead of the original '{value}'.\n"
                f"To resolve, either:\n"
                f"(a) Change snake_case string from '{value}' to '{back}' to allow lossless\n"
                f"    snake_case to PascalCase roundtrip or\n"
                f"(b) Add the intended snake_case and PascalCase pair to case_conversion_rules in settings.\n"
            )
        return result

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
    def any_to_snake_case(cls, value: str | None) -> str | None:
        """Convert any string to valid snake_case on a best-effort basis.

        Handles PascalCase, camelCase, UPPER_CASE, Title Case, kebab-case,
        and mixed formats. Uppercase acronym runs are split at word boundaries
        (e.g., HTTPResponse -> http_response). The result is guaranteed to
        pass check_snake_case.
        """
        if cls.is_empty(value):
            return value
        # Replace non-alphanumeric characters (except dots) with underscores
        result = _NON_ALNUM_DOT_RE.sub("_", value)
        # Split uppercase runs at word boundaries (e.g., HTTPResponse -> HTTP_Response)
        result = _UPPER_RUN_BOUNDARY_RE.sub(r"\1_\2", result)
        # Split at lowercase->uppercase/digit boundaries (e.g., camelCase -> camel_Case)
        result = _PASCAL_TO_SNAKE_RE.sub(r"\1_\2", result)
        # Lowercase
        result = result.lower()
        # Collapse multiple underscores and strip leading/trailing
        result = _MULTI_UNDERSCORE_RE.sub("_", result).strip("_")
        # Remove underscores after digits (digit separator rule)
        result = _DIGIT_UNDERSCORE_VIOLATIONS_RE.sub("", result)
        # Round-trip normalize to ensure validity
        result = cls._pascal_to_snake_unchecked(cls._snake_to_pascal_unchecked(result))
        return result

    @classmethod
    def any_to_pascal_case(cls, value: str | None) -> str | None:
        """Convert any string to valid PascalCase on a best-effort basis.

        Handles snake_case, camelCase, UPPER_CASE, Title Case, kebab-case,
        and mixed formats. The result is guaranteed to pass check_pascal_case.
        """
        if cls.is_empty(value):
            return value
        snake = cls.any_to_snake_case(value)
        return cls._snake_to_pascal_unchecked(snake)

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
            if value in _PASCAL_TO_SNAKE_DICT:
                return
            back = cls._snake_to_pascal_unchecked(cls._pascal_to_snake_unchecked(value))
        elif format_ == "snake_case":
            if value in _SNAKE_TO_PASCAL_DICT:
                return
            back = cls._pascal_to_snake_unchecked(cls._snake_to_pascal_unchecked(value))
        elif format_ == "UPPER_CASE":
            if value.lower() in _SNAKE_TO_PASCAL_DICT:
                return
            back = cls._pascal_to_snake_unchecked(cls._snake_to_pascal_unchecked(value.lower())).upper()
        else:
            return
        if back != value:
            cls._ensure_conversion_rules_loaded()
            if format_ == "PascalCase" and value in _PASCAL_TO_SNAKE_DICT:
                return
            if format_ == "snake_case" and value in _SNAKE_TO_PASCAL_DICT:
                return
            if format_ == "UPPER_CASE" and value.lower() in _SNAKE_TO_PASCAL_DICT:
                return
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
        result = _ALPHA_UPPER_RUN_BOUNDARY_RE.sub(r"\1_\2", value)
        return _PASCAL_TO_SNAKE_RE.sub(r"\1_\2", result).lower()

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

    @classmethod
    def _ensure_conversion_rules_loaded(cls) -> None:
        """Load case conversion rules from CaseSettings into the in-memory dicts. No-op if already loaded."""
        global _CONVERSION_RULES_LOADED
        if _CONVERSION_RULES_LOADED:
            return

        # Delayed import to avoid circular dependency
        from cl.runtime.settings.case_settings import CaseSettings

        # Get conversion rules from all settings sources
        snake_to_pascal, pascal_to_snake = CaseSettings.get_combined_conversion_rules()
        for snake, pascal in snake_to_pascal.items():
            if snake in _SNAKE_TO_PASCAL_DICT and _SNAKE_TO_PASCAL_DICT[snake] != pascal:
                raise RuntimeError(
                    f"Conflicting case conversion for snake_case value '{snake}': "
                    f"existing mapping '{snake}' -> '{_SNAKE_TO_PASCAL_DICT[snake]}' "
                    f"conflicts with settings entry '{snake}' -> '{pascal}'."
                )
            if pascal in _PASCAL_TO_SNAKE_DICT and _PASCAL_TO_SNAKE_DICT[pascal] != snake:
                raise RuntimeError(
                    f"Conflicting case conversion for PascalCase value '{pascal}': "
                    f"existing mapping '{pascal}' -> '{_PASCAL_TO_SNAKE_DICT[pascal]}' "
                    f"conflicts with settings entry '{pascal}' -> '{snake}'."
                )
            _SNAKE_TO_PASCAL_DICT[snake] = pascal
            _PASCAL_TO_SNAKE_DICT[pascal] = snake

        _CONVERSION_RULES_LOADED = True
