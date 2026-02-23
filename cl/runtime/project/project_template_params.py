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
from typing import Any, Sequence, Mapping

from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class ProjectTemplateParams(DataclassMixin):
    """Parameters passed as kwargs to Jinja2 templates in init_project."""

    package_dirs: Sequence[str] = required()
    """Ordered package directory names from PackageSettings."""

    combined_package_dependencies: Sequence[str] | None = None
    """Combined dependencies from all packages."""

    combined_test_dependencies: Sequence[str] | None = None
    """Combined test dependencies from all packages."""

    def to_dict(self) -> Mapping[str, Any]:
        """Convert all fields to a dict suitable for Jinja2 template rendering."""
        return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}  # TODO(Claude): Use DataSerializer?
