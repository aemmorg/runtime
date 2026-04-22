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

from typing import Any
from cl.runtime.records.for_pydantic.pydantic_mixin import PydanticMixin


class LoadRecordResponse(PydanticMixin):
    """Load record response."""

    record: Any | None = None
    """Serialized loaded record, actually RecordMixin."""

    type_spec: Any | None = None
    """Serialized type spec for record, actually TypeSpec."""

    dependencies: dict[str, Any] | None = None
    """Serialized dependencies for record, actually dict[typename: TypeSpec]."""
