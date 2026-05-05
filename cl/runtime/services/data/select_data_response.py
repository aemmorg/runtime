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


class SelectDataResponse(PydanticMixin):
    """Select data response."""

    data: list[Any]
    """Selected data."""

    type_spec: dict[str, Any]
    """Serialized type spec for the selected data type."""

    dependencies: dict[str, Any]
    """Serialized dependencies for record, actually dict[typename: TypeSpec]."""

    query_schemas: dict[str, dict[str, Any]] | None = None
    """Serialized query type schemas indexed by query type name, None if no query types exist for the table."""

    schema: dict[str, Any] | None = None  # TODO: Remove backward compatibility with pre-v2.0.0 frontends
    """Flattened dict of all type specs keyed by type name (backward compatibility with pre-v2.0.0 frontends)."""

    base_type: str | None = None  # TODO: Remove backward compatibility with pre-v2.0.0 frontends
    """Root type name (backward compatibility with pre-v2.0.0 frontends)."""
