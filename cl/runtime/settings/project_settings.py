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
from typing import Sequence
from typing_extensions import final  # TODO: !!! Do not import from typing_extensions
from cl.runtime.prebuild.license_kind import LicenseKind
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class ProjectSettings(Settings):
    """Project settings used to generate pyproject.toml and other build config files and scripts."""

    project_name: str = required()
    """Field 'name' under [project] in pyproject.toml."""

    project_version: str = required()
    """Project 'version' in pyproject.toml, defaults to the version of the last package listed in package_dirs."""  # TODO(Claude): Implement in __init to set to this value if not specified

    project_description: str | None = None
    """Field 'description' under [project] in pyproject.toml, skip if not specified."""

    project_required_python: str | None = None
    """Field 'requires-python' under [project] in pyproject.toml, skip if not specified."""

    project_license_kind: LicenseKind | None = None
    """Determines license-related settings, try to match LICENSE file checksum if not specified."""  # TODO(Claude): Implement in __init to set to this value if not specified

    project_license: str | None = None
    """Field 'license' under [project] in pyproject.toml, try to match LICENSE file checksum if not specified."""

    project_authors: str | None = None
    """Field 'authors' under [project] in pyproject.toml, try to read from COPYRIGHT if not specified."""

    project_classifiers: Sequence[str] = required()
    """Field 'classifiers' under [project] in pyproject.toml, skip if not specified."""

    project_urls_repository: Sequence[str] = required()
    """Field 'repository' under [project.urls] in pyproject.toml, skip if not specified."""

    project_dependencies: Sequence[str] = required()
    """Field 'dependencies' under [project] in pyproject.toml, skip if not specified."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
