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
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.typename import typename
from cl.runtime.schema.field_spec import FieldSpec
from cl.runtime.schema.handler_spec import HandlerSpec
from cl.runtime.schema.type_spec import TypeSpec


@dataclass(slots=True, kw_only=True)
class DataSpec(TypeSpec):
    """Provides information about a class with fields."""

    fields: list[FieldSpec] = required()
    """Fields in class declaration order."""

    handlers: list[HandlerSpec] | None = None
    """Handlers declared on this type."""

    label: str | None = None
    """Display label for the type."""

    preserve_in_root_dataset: bool | None = None
    """If True, force replace dataset with the root dataset for DataSource operations."""

    hidden: bool | None = None
    """If True, type is hidden in the UI."""

    readonly: bool | None = None
    """If True, type is read-only in the UI."""

    interactive: bool | None = None
    """True if the type is a descendant of InteractiveMixin."""

    editable: bool | None = None
    """If True, the current user has permission to insert/replace records of this type."""

    deletable: bool | None = None
    """If True, the current user has permission to delete records of this type."""

    display_kind: str | None = None
    """Display kind for the type in the UI."""

    def __init(self) -> None:
        """Set label from type name when not explicitly provided (invoked by build())."""
        if self.label is None:
            self.label = CaseUtil.pascal_to_title_case(typename(self.type_))
