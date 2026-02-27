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
from cl.runtime.project.project_util import ProjectUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.settings.dynaconf_loader import DynaconfLoader
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class ProjectSettings(Settings):
    """Project settings used to generate pyproject.toml and other build config files and scripts."""

    project_name: str | None = None
    """Field 'name' under [project] in pyproject.toml."""

    project_dirs: Mapping[str, str] = required()
    """
    Ordered mapping of package source namespace to package directory relative to project root
    where dependent packages follow the packages they depend on.
    """

    project_version: str = required()
    """Project 'version' in pyproject.toml, defaults to the version of the last package listed in project_dirs."""  # TODO(Claude): !! Implement in __init to set to this value if not specified

    project_description: str | None = None
    """Field 'description' under [project] in pyproject.toml, skip if not specified."""

    project_required_python: str | None = None
    """Field 'requires-python' under [project] in pyproject.toml, skip if not specified."""

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

    def get_packages(self) -> tuple[str, ...]:
        """Ordered tuple of package namespaces (keys) from project_dirs mapping."""
        return tuple(self.project_dirs.keys())

    def get_package_dirs(self) -> tuple[str, ...]:
        """Ordered tuple of package directories (values) from project_dirs mapping with duplicates removed."""
        return tuple(dict.fromkeys(self.project_dirs.values()))

    def configure_paths(self) -> None:
        """
        Ensure all source and stub directories are in sys.path and PYTHONPATH

        Directories are only added if they are not already present,
        irrespective of relative vs. absolute path format or OS separators.
        """

        # Absolute paths to source and stub directories for all packages
        project_root = ProjectUtil.get_project_root()
        package_paths = tuple(os.path.join(project_root, x) for x in self.project_dirs.values())
        package_paths = self._normalize_paths(package_paths)

        # Add to sys.path without duplicates
        sys_path_set = set(self._normalize_paths(sys.path))
        for path in self._normalize_paths(list(self.project_dirs.values())):
            if path not in sys_path_set:
                # Add path from package_paths
                sys.path.append(path)

        # Add to PYTHONPATH without duplicates
        python_path_str = DynaconfLoader.get_envvar_value("PYTHONPATH", "")
        python_path_set = set(self._normalize_paths(python_path_str.split(os.pathsep)))
        python_path_added = False
        for path in package_paths:
            if path not in python_path_set:
                python_path_added = True
                if python_path_str:
                    # Add separator unless empty
                    python_path_str += os.pathsep
                # Add path from package_paths
                python_path_str += path
        if python_path_added:
            # Only if paths have been added
            os.environ["PYTHONPATH"] = python_path_str

    @classmethod
    def _normalize_paths(cls, paths: Sequence[str]) -> tuple[str, ...]:
        """Convert paths to canonical format."""
        return tuple(os.path.abspath(os.path.normpath(p)) for p in paths)
