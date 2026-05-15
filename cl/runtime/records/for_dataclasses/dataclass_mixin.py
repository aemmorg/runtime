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
import inspect
import typing
from abc import ABC
from types import FunctionType
from types import MethodType
from typing import Self
from typing import get_type_hints
from memoization import cached
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.protocols import is_dashboard_type
from cl.runtime.records.protocols import is_interactive_type
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.protocols import is_record_type
from cl.runtime.records.protocols import is_singleton_type
from cl.runtime.records.typename import typename
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.field_spec import FieldSpec
from cl.runtime.schema.handler_param_spec import HandlerParamSpec
from cl.runtime.schema.handler_spec import HandlerSpec
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.slots_util import SlotsUtil


class DataclassMixin(DataMixin, ABC):
    """Implements abstract methods in DataMixin for dataclass-based data, key or record classes."""

    __slots__ = ()

    @classmethod
    @cached
    def get_field_names(cls) -> tuple[str, ...]:
        return SlotsUtil.get_field_names(cls)  # TODO: !!!!!! Replace with get_type_spec

    @classmethod
    @cached
    def get_type_spec(cls) -> DataSpec:
        if not dataclasses.is_dataclass(cls):
            raise RuntimeError(f"{typename(cls)} is derived from DataclassMixin but has no @dataclass decorator.")

        # Determine key field names for the type
        key_field_names: set[str] = set()
        if is_key_type(cls):
            key_field_names = {f.name for f in dataclasses.fields(cls) if not f.name.startswith("_")}
        elif is_record_type(cls) and hasattr(cls, "get_key_type"):
            key_type = cls.get_key_type()
            if key_type is not None:
                key_names = key_type.get_field_names()
                if key_names is not None:
                    key_field_names = set(key_names)

        # Create the list of field specs
        fields = [
            cls._create_field_spec(
                field,
                containing_type=cls,
                key=True if field.name in key_field_names else None,
            )
            for field in dataclasses.fields(cls)  # noqa: type=ignore
            if not field.name.startswith("_")
        ]

        # Discover handlers (run_* / view_*) from class methods
        handlers = cls._create_handler_specs()

        return DataSpec(
            type_=cls,
            fields=fields,
            handlers=handlers if handlers else None,
            interactive=True if is_interactive_type(cls) else None,
            display_kind=("Dashboard" if is_dashboard_type(cls) else "Singleton" if is_singleton_type(cls) else None),
        ).build()

    @classmethod
    def _create_field_spec(
        cls,
        field: dataclasses.Field,
        *,
        containing_type: type[Self],
        field_type_alias: typing.TypeAlias | None = None,
        key: bool | None = None,
    ) -> FieldSpec:
        """Create FieldSpec from dataclasses Field."""

        metadata_dict = dict(field.metadata)

        if field_type_alias is not None:
            field_type = field_type_alias
        elif isinstance(field.type, str):
            # Resolve str type annotation. This happens when 'from __future__ import annotations' is used.
            resolved_type_hints = get_type_hints(cls, include_extras=True)
            field_type = resolved_type_hints[field.name]
        else:
            field_type = field.type

        result = FieldSpec.create(
            field_name=field.name,
            field_type_alias=field_type,
            containing_type=containing_type,
            field_optional=metadata_dict.pop("optional", None),
            field_subtype=metadata_dict.pop("subtype", None),
            field_alias=metadata_dict.pop("name", None),  # TODO: ! Add support for name
            field_label=metadata_dict.pop("label", None),
            field_formatter=metadata_dict.pop("formatter", None),  # TODO: ! Add support for formatter
            descending=metadata_dict.pop("descending", None),
            key=key,
        ).build()

        if len(metadata_dict) > 0:
            unused_metadata_str = "\n".join(f"{k}:{v}" for k, v in metadata_dict)
            raise RuntimeError(f"Unrecognized keys in dataclass field metadata:\n{unused_metadata_str}")
        return result

    @classmethod
    def _create_handler_specs(cls) -> list[HandlerSpec]:
        """Discover handlers (run_* / view_* methods) and return a list of HandlerSpec."""
        handler_specs: list[HandlerSpec] = []

        for member_name in dir(cls):
            if member_name.startswith("_"):
                continue

            try:
                member = getattr(cls, member_name)
            except AttributeError:
                continue
            if not (inspect.isfunction(member) or inspect.ismethod(member)):
                continue

            if member_name.startswith("run_"):
                handler_type = "job"
            elif member_name.startswith("view_"):
                handler_type = "viewer"
            else:
                continue

            handler_specs.append(cls._create_handler_spec(member_name, member, handler_type))

        return handler_specs

    @classmethod
    def _create_handler_spec(
        cls, member_name: str, member: FunctionType | MethodType, handler_type: str
    ) -> HandlerSpec:
        """Create a single HandlerSpec from a method."""

        params = cls._create_handler_param_specs(member)

        func = member.__func__ if isinstance(member, MethodType) else member
        try:
            type_hints = get_type_hints(func, include_extras=True)
        except Exception:
            type_hints = {}
        return_annotation = type_hints.get("return", None)

        return_type = None
        if return_annotation is not None and return_annotation is not type(None):
            try:
                return_type = TypeHint.for_type_alias(
                    type_alias=return_annotation,
                    field_name="return",
                    containing_type=cls,
                )
            except Exception:
                # Unsupported return types don't block handler discovery
                return_type = None

        return HandlerSpec(
            name=CaseUtil.snake_to_pascal_case(member_name),
            type_=handler_type,
            comment=member.__doc__,
            static=isinstance(inspect.getattr_static(cls, member_name), (staticmethod, classmethod)),
            params=params if params else None,
            return_type=return_type,
        ).build()

    @classmethod
    def _create_handler_param_specs(cls, method: FunctionType | MethodType) -> list[HandlerParamSpec]:
        """Extract HandlerParamSpec list from a method's signature."""
        # Local import to avoid circular dependency (ParamInfo inherits DataclassMixin)
        from cl.runtime.records.param_info import ParamInfo

        func = method.__func__ if isinstance(method, MethodType) else method

        try:
            type_hints = get_type_hints(func, include_extras=True)
        except Exception:
            type_hints = {}

        sig = inspect.signature(method)
        params: list[HandlerParamSpec] = []

        for param_name, param in sig.parameters.items():
            if param_name in {"self", "cls"}:
                continue

            annotation = type_hints.get(param_name, param.annotation)
            if annotation is inspect.Parameter.empty:
                continue

            # Strip Annotated wrapper to extract ParamInfo label if present
            param_label: str | None = None
            if typing.get_origin(annotation) is typing.Annotated:
                annotation_args = typing.get_args(annotation)
                annotation = annotation_args[0]
                param_info = next((arg for arg in annotation_args[1:] if isinstance(arg, ParamInfo)), None)
                if param_info is not None:
                    param_label = param_info.label

            try:
                type_hint = TypeHint.for_type_alias(
                    type_alias=annotation,
                    field_name=param_name,
                    containing_type=cls,
                )
            except Exception:
                # Skip params with unsupported annotations rather than aborting handler discovery
                continue

            param_spec = HandlerParamSpec(
                name=CaseUtil.snake_to_pascal_case(param_name),
                type_hint=type_hint,
                label=param_label,
            ).build()
            params.append(param_spec)

        return params
