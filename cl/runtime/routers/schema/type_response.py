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

from collections import deque
from typing import Any
from pydantic import BaseModel
from pydantic import ConfigDict
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.protocols import is_mixin_type
from cl.runtime.records.typename import typename
from cl.runtime.routers.schema.type_request import TypeRequest
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.schema.type_schema import TypeSchema
from cl.runtime.schema.type_spec import TypeSpec
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers


class TypeResponse(BaseModel):
    """Response data class for the /schema/type route."""

    type_spec: dict[str, Any]
    """Serialized type spec for the requested type."""

    dependencies: dict[str, Any]
    """Serialized dependencies, actually dict[typename: TypeSpec]."""

    model_config = ConfigDict(alias_generator=CaseUtil.snake_to_pascal_case, populate_by_name=True)

    @classmethod
    def get_type(
        cls,
        request: TypeRequest,
        *,
        include_key: bool = True,
        include_data: bool = True,
        include_enum: bool = True,
        include_fields: bool = True,
        include_handlers: bool = True,
    ) -> "TypeResponse":
        """Implements /schema/type route."""

        type_ = TypeInfo.from_type_name(request.type_name)
        type_spec = type_.get_type_spec()
        dependency_dict = cls.get_dependency_dict(
            type_spec,
            include_key=include_key,
            include_data=include_data,
            include_enum=include_enum,
            include_fields=include_fields,
            include_handlers=include_handlers,
        )

        serialized_type_spec = BootstrapSerializers.FOR_UI.serialize(type_spec)
        serialized_dependencies = {
            type_name: BootstrapSerializers.FOR_UI.serialize(dep_spec)
            for type_name, dep_spec in dependency_dict.items()
        }
        return TypeResponse(type_spec=serialized_type_spec, dependencies=serialized_dependencies)

    @classmethod
    def get_dependency_dict(
        cls,
        type_spec: TypeSpec,
        *,
        include_key: bool = True,
        include_data: bool = True,
        include_enum: bool = True,
        include_fields: bool = True,
        include_handlers: bool = True,
    ) -> dict[str, TypeSpec]:
        """Build a dict of transitive type dependencies by walking fields and handler params via BFS.

        Args:
            type_spec: Root type whose dependencies are collected
            include_key: If True, include KEY leaf types in the result
            include_data: If True, include DATA and RECORD leaf types in the result
            include_enum: If True, include ENUM leaf types in the result
            include_fields: If True, include dependencies from fields of the root type
            include_handlers: If True, include dependencies from handler parameters of the root type
        """

        result: dict[str, TypeSpec] = {}

        if not isinstance(type_spec, DataSpec):
            return result

        def _add_leaf(type_hint) -> TypeSpec | None:
            """Walk past containers to the leaf type and add it to result. Returns newly added TypeSpec or None."""
            leaf = type_hint
            while leaf is not None and leaf.type_kind == TypeKind.CONTAINER:
                leaf = leaf.remaining
            if leaf is None:
                return None
            if leaf.type_kind == TypeKind.ENUM and include_enum:
                pass
            elif leaf.type_kind == TypeKind.KEY and include_key:
                pass
            elif leaf.type_kind in (TypeKind.DATA, TypeKind.RECORD) and include_data:
                pass
            else:
                return None
            if is_mixin_type(leaf.schema_type):
                return None
            key = typename(leaf.schema_type)
            if key not in result:
                spec = TypeSchema.for_type(leaf.schema_type)
                result[key] = spec
                return spec
            return None

        queue: deque[DataSpec] = deque([type_spec])
        is_root = True

        while queue:
            current = queue.popleft()

            if include_fields or not is_root:
                for field in current.fields:
                    new_spec = _add_leaf(field.field_type_hint)
                    if new_spec is not None and isinstance(new_spec, DataSpec):
                        queue.append(new_spec)

            if is_root and include_handlers:
                if current.handlers is not None:
                    for handler in current.handlers:
                        if handler.params is not None:
                            for param in handler.params:
                                new_spec = _add_leaf(param.type_hint)
                                if new_spec is not None and isinstance(new_spec, DataSpec):
                                    queue.append(new_spec)
            is_root = False

        return result
