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
from memoization import cached
from parse import parse
from typing_extensions import final
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.settings.project_settings import ProjectSettings
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class TypeSettings(Settings):
    """Settings for type name rules that map qualname patterns to type name patterns."""

    type_name_rules: Mapping[str, str] | None = None
    """
    Mapping of f-string patterns for qualname in module.module.ClassName format
    to f-string patterns for TypeName in PascalCase format.
    """

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

    @classmethod
    @cached
    def get_type_name_rules(cls) -> tuple[tuple[str, str], ...]:
        """Gather type_name_rules from all packages followed by project, check for duplicates.

        Returns:
            Ordered tuple of (key_pattern, value_pattern) pairs where packages come first
            in the order of project_dirs, followed by project-level rules.
        """

        packages = ProjectSettings.instance().get_packages()

        all_rules: list[tuple[str, str]] = []
        seen_keys: dict[str, str] = {}

        # Gather from packages in order of project_dirs, then project (package=None)
        sources: list[tuple[str | None, str]] = [(pkg, pkg) for pkg in packages] + [(None, "project")]

        for package, source_name in sources:
            settings = cls.instance(package=package)

            if settings.type_name_rules is None:
                continue

            for key, value in settings.type_name_rules.items():
                if key in seen_keys:
                    raise RuntimeError(
                        f"Duplicate type_name_rules key '{key}' found in "
                        f"'{source_name}' and '{seen_keys[key]}'."
                    )
                seen_keys[key] = source_name
                all_rules.append((key, value))

        return tuple(all_rules)

    @classmethod
    @cached
    def get_type_name(cls, qual_name: str) -> str:
        """Match qual_name to type name rules patterns, last match wins.

        Args:
            qual_name: Fully qualified name in module.module.ClassName format

        Returns:
            Type name produced by the last matching pattern, or the class name
            (last dot-delimited segment of qual_name) if no pattern matches.
        """

        rules = cls.get_type_name_rules()

        # Default: class name is the last segment of qual_name
        result = qual_name.rsplit(".", 1)[-1]

        # Try each rule, last match wins
        for key_pattern, value_pattern in rules:
            parsed = parse(key_pattern, qual_name)
            if parsed is not None:
                pascal_named = {
                    k: CaseUtil.snake_to_pascal_case(v) if CaseUtil.is_snake_case(v) else v
                    for k, v in parsed.named.items()
                }
                result = value_pattern.format(**pascal_named)

        return result
