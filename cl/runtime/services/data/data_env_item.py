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

from cl.runtime.records.for_pydantic.pydantic_mixin import PydanticMixin


class DataEnvItem(PydanticMixin):
    """Single data environment screen item with optional nested children."""

    name: str
    """Data environment name."""

    description: str | None = None
    """Human-readable description (optional)."""

    server: str | None = None
    """Server hosting this data environment (optional)."""

    child_data_envs: list["DataEnvItem"] | None = None
    """Nested child data environments (optional)."""
