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

from dataclasses import dataclass
from typing import Mapping
from typing import final
from cl.runtime.settings.project_settings import ProjectSettings
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class CaseSettings(Settings):
    """Settings for case conversion rules that cannot be derived algorithmically."""

    case_conversion_rules: Mapping[str, str] | None = None
    """Mapping of snake_case to PascalCase for conversions that do not roundtrip algorithmically."""

    @classmethod
    def get_combined_conversion_rules(cls) -> tuple[dict[str, str], dict[str, str]]:
        """
        Gather case_conversion_rules across all packages and project settings,
        validate uniqueness, and return (snake_to_pascal, pascal_to_snake) dicts.
        """

        snake_to_pascal: dict[str, str] = {}
        pascal_to_snake: dict[str, str] = {}
        snake_to_source: dict[str, str] = {}
        pascal_to_source: dict[str, str] = {}

        packages = ProjectSettings.instance().get_packages()

        # Gather from each package and from project-level (None)
        for package in (*packages, None):
            settings = cls.instance(package=package)
            if settings.case_conversion_rules is None:
                continue
            source = f"package '{package}'" if package is not None else "project settings"
            for snake, pascal in settings.case_conversion_rules.items():
                cls._add_rule(snake, pascal, source, snake_to_pascal, pascal_to_snake, snake_to_source, pascal_to_source)

        return snake_to_pascal, pascal_to_snake

    @classmethod
    def _add_rule(
        cls,
        snake: str,
        pascal: str,
        source: str,
        snake_to_pascal: dict[str, str],
        pascal_to_snake: dict[str, str],
        snake_to_source: dict[str, str],
        pascal_to_source: dict[str, str],
    ) -> None:
        """Add a rule to the dicts, raising on conflicts (identical duplicates are allowed)."""

        # Check for conflicting snake_case key
        if snake in snake_to_pascal:
            existing_pascal = snake_to_pascal[snake]
            if existing_pascal != pascal:
                existing_source = snake_to_source[snake]
                raise RuntimeError(
                    f"Conflicting case conversion for snake_case value '{snake}' in {source}\n"
                    f"maps to '{pascal}' but already maps to '{existing_pascal}' in {existing_source}."
                )
            # Identical duplicate, skip
            return

        # Check for conflicting pascal_case value
        if pascal in pascal_to_snake:
            existing_snake = pascal_to_snake[pascal]
            if existing_snake != snake:
                existing_source = pascal_to_source[pascal]
                raise RuntimeError(
                    f"Conflicting case conversion for PascalCase value '{pascal}' in {source}\n"
                    f"maps to '{snake}' but already maps to '{existing_snake}' in {existing_source}."
                )

        snake_to_pascal[snake] = pascal
        pascal_to_snake[pascal] = snake
        snake_to_source[snake] = source
        pascal_to_source[pascal] = source
