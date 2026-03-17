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

import os
from dataclasses import dataclass
from typing import ClassVar
from cl.runtime.project.resources_util import ResourcesUtil

_CASE_CONVERSION_RULE_HEADERS = ("SnakeCase", "PascalCase")
"""Headers of CaseConversionRule preload file."""


@dataclass(slots=True, kw_only=True)
class CaseConversionRule:
    """Rule for case conversion between snake_case and PascalCase that cannot be derived algorithmically."""

    snake_case: str
    """Value in snake_case format."""

    pascal_case: str
    """Value in PascalCase format."""

    _snake_to_pascal: ClassVar[dict[str, str] | None] = None
    """Dictionary mapping snake_case to PascalCase."""

    _pascal_to_snake: ClassVar[dict[str, str] | None] = None
    """Dictionary mapping PascalCase to snake_case."""

    @classmethod
    def get_pascal_case(cls, snake_case: str) -> str | None:
        """Return PascalCase for the given snake_case, or None if not found."""
        cls.ensure_loaded()
        return cls._snake_to_pascal.get(snake_case)

    @classmethod
    def get_snake_case(cls, pascal_case: str) -> str | None:
        """Return snake_case for the given PascalCase, or None if not found."""
        cls.ensure_loaded()
        return cls._pascal_to_snake.get(pascal_case)

    @classmethod
    def ensure_loaded(cls) -> None:
        """Load the data from CaseConversionRule.csv if not already loaded, do not reload."""

        if cls._snake_to_pascal is not None:
            # Already loaded, exit early
            return

        # Initialize empty dicts
        cls._snake_to_pascal = {}
        cls._pascal_to_snake = {}

        # Read from the cache file
        cache_file_path = cls._get_file_path()
        if not os.path.exists(cache_file_path):
            # File does not exist, keep empty dicts
            return

        with open(cache_file_path, "r", encoding="utf-8") as file:
            rows = file.readlines()

        for row_index, row in enumerate(rows):

            # Skip empty lines
            if not row.strip():
                continue

            # Remove leading and trailing whitespace from each comma-separated token
            row_tokens = tuple(x.strip() for x in row.split(","))

            if row_index == 0:
                # Check that the header row has expected values
                if row_tokens != _CASE_CONVERSION_RULE_HEADERS:
                    actual_headers_str = ", ".join(row_tokens)
                    expected_headers_str = ", ".join(_CASE_CONVERSION_RULE_HEADERS)
                    raise RuntimeError(
                        f"CaseConversionRule preload file has invalid headers.\n"
                        f"Preload file: {cache_file_path}\n"
                        f"Actual headers: {actual_headers_str}\n"
                        f"Expected headers: {expected_headers_str}\n"
                    )
            else:
                # Parse a case conversion rule row
                if len(row_tokens) == len(_CASE_CONVERSION_RULE_HEADERS):
                    snake_case, pascal_case = row_tokens

                    # Check for duplicate snake_case entries
                    if snake_case in cls._snake_to_pascal:
                        raise RuntimeError(
                            f"Duplicate snake_case entry '{snake_case}' in CaseConversionRule.csv."
                        )

                    # Check for duplicate pascal_case entries
                    if pascal_case in cls._pascal_to_snake:
                        raise RuntimeError(
                            f"Duplicate PascalCase entry '{pascal_case}' in CaseConversionRule.csv."
                        )

                    cls._snake_to_pascal[snake_case] = pascal_case
                    cls._pascal_to_snake[pascal_case] = snake_case
                else:
                    expected_num_tokens = len(_CASE_CONVERSION_RULE_HEADERS)
                    actual_num_tokens = len(row_tokens)
                    raise RuntimeError(
                        f"Invalid number of comma-delimited tokens {actual_num_tokens} in CaseConversionRule, "
                        f"should be {expected_num_tokens}.\n"
                        f"Sample row: snake_case_value,PascalCaseValue\n"
                        f"Invalid row: {row.strip()}\n"
                    )

    @classmethod
    def clear(cls) -> None:
        """Clear cache before reloading."""
        cls._snake_to_pascal = None
        cls._pascal_to_snake = None

    @classmethod
    def _get_file_path(cls) -> str:
        """Get the filename for the case conversion rule file."""
        result = os.path.join(ResourcesUtil.get_bootstrap_root(), "CaseConversionRule.csv")
        return result
