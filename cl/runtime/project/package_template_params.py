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

import dataclasses
from dataclasses import dataclass
from typing import Any
from typing import Mapping
from typing import Sequence
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class PackageTemplateParams(DataclassMixin):
    """Parameters passed as kwargs to Jinja2 templates in init_packages."""

    package_copyright: str = required()
    """Raw contents of the COPYRIGHT file at package root."""

    package_name: str = required()
    """Readable package name for pyproject.toml, e.g., 'Runtime'."""

    package_namespace: str = required()
    """Dot-delimited package namespace, e.g., 'cl.runtime'."""

    package_path: str = required()
    """Slash-delimited package namespace, e.g., 'cl/runtime'."""

    package_version: str = required()
    """Package version string."""

    package_description: str = required()
    """Package description for pyproject.toml."""

    package_requires_python: str | None = None
    """Python version constraint, e.g., '>=3.11'."""

    package_license: str = required()
    """License name, e.g., 'Apache Software License'."""

    package_authors: str = required()
    """Authors string extracted from COPYRIGHT or settings."""

    package_classifiers: Sequence[str] | None = None
    """PyPI classifiers for pyproject.toml."""

    package_urls: Mapping[str, str] = required()
    """URL mapping for pyproject.toml (e.g., Repository -> URL)."""

    package_dependencies: Sequence[str] | None = None
    """Direct package dependencies."""

    combined_package_dependencies: Sequence[str] | None = None
    """Combined dependencies from current and all earlier packages."""

    combined_test_dependencies: Sequence[str] | None = None
    """Combined test dependencies from current and all earlier packages."""

    package_has_shared_data: bool | None = None
    """If True, include py.typed marker in pyproject.toml."""  # TODO(Claude): Why py.typed if it is data rather than code that is shared?

    package_has_mypy: bool | None = None
    """If True, include mypy configuration section in pyproject.toml."""

    main_packages: Sequence[str] | None = None
    """All main package namespaces up to and including the current package."""

    stub_packages: Sequence[str] | None = None
    """Stub package namespaces for all included main packages."""

    isort_known_packages: Sequence[Mapping[str, str]] | None = None
    """Isort known_* entries for main packages, each with 'key', 'value', 'section'."""

    isort_known_stubs: Sequence[Mapping[str, str]] | None = None
    """Isort known_* entries for stub packages, each with 'key', 'value', 'section'."""

    isort_sections: Sequence[str] | None = None
    """Complete ordered list of isort sections."""

    def to_dict(self) -> dict[str, Any]:
        """Convert all fields to a dict suitable for Jinja2 template rendering."""
        return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}  # TODO(Claude): Use DataSerializer?
