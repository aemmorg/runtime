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
import sys
from dataclasses import dataclass
from typing import Mapping
from typing import Sequence
from typing_extensions import final  # TODO: !!! Do not import from typing_extensions
from cl.runtime.project.project_checks import ProjectChecks
from cl.runtime.project.project_util import ProjectUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.settings.dynaconf_loader import DynaconfLoader
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class PackageSettings(Settings):
    """Package-specific settings, usual Dynaconf overrides from env vars or .env do not apply."""

    package_name: str | None = None
    """Field 'name' under [project] in pyproject.toml of the package."""

    package_namespace: str = required()
    """Namespace of the package, e.g. 'cl.runtime'."""

    package_description: str | None = None
    """Field 'description' under [project] in pyproject.toml of the package, skip if not specified."""

    package_requires_python: str | None = None
    """Field 'requires-python' under [project] in pyproject.toml of the package, skip if not specified."""

    package_license: str | None = None
    """Field 'license' under [project] in pyproject.toml of the package, match based on LICENSE file checksum if not specified."""

    package_authors: str | None = None
    """Field 'authors' under [project] in pyproject.toml of the package, try to read from COPYRIGHT if not specified."""

    package_urls: Mapping[str, str] | None = None
    """Mapping under [project.urls] in pyproject.toml of the package, skip if not specified."""

    package_classifiers: Sequence[str] | None = None
    """Field 'classifiers' under [project] in pyproject.toml of the package, skip if not specified."""

    package_stubs_namespace: str = "stubs.{package_namespace}"
    """Stubs namespace of the package, e.g. 'stubs.cl.runtime' (defaults to stubs.{package_namespace})."""

    package_source_dir: str = "."
    """Source dir relative to project root (defaults to '.', i.e. placement directly under project root)."""

    package_stubs_dir: Mapping[str, str] = "stubs"
    """Stubs dir relative to project root (defaults to 'stubs')."""

    package_tests_dir: Mapping[str, str] = "tests"
    """Tests dir relative to project root (defaults to 'tests')."""

    package_has_shared_data: bool = False
    """Whether to include [tool.hatch.build.targets.wheel.shared-data] section for py.typed marker."""

    package_has_mypy: bool = False
    """Whether to include [tool.mypy] section in pyproject.toml of the package."""

    package_dependencies: Sequence[str] | None = None
    """Field 'dependencies' under [project] in pyproject.toml of the package, combined across packages for venv setup."""

    package_test_dependencies: Sequence[str] | None = None
    """Included when testing, combined across packages."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Perform variable substitution in package_stubs_namespace if package_namespace is set
        if self.package_namespace is not None:
            self.package_stubs_namespace = self.package_stubs_namespace.format(package_namespace=self.package_namespace)

        # Validate and check for duplicates in package dependencies
        if self.package_dependencies is not None:
            self.package_dependencies = tuple(self.package_dependencies)
            ProjectChecks.guard_requirements(self.package_dependencies)
            self._check_duplicates(self.package_dependencies, "package_dependencies")

        # Validate and check for duplicates in package test dependencies
        if self.package_test_dependencies is not None:
            self.package_test_dependencies = tuple(self.package_test_dependencies)
            self._check_duplicates(self.package_test_dependencies, "package_test_dependencies")

    @classmethod
    def _check_duplicates(cls, deps: Sequence[str], field_name: str) -> None:
        """Raise an error if the dependency list contains duplicates within a single package."""
        seen = set()
        for dep in deps:
            # Normalize to lowercase for comparison
            dep_lower = dep.lower()
            if dep_lower in seen:
                raise RuntimeError(f"Duplicate entry '{dep}' in {field_name}.")
            seen.add(dep_lower)
