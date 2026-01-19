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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.protocols import is_record_type
from cl.runtime.records.record_panel import RecordPanel
from cl.runtime.schema.handler_declare_decl import HandlerDeclareDecl
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.views.view_persistence_util import ViewPersistenceUtil

_KEY_SERIALIZER = KeySerializers.DELIMITED
"""Used for key serialization."""


@dataclass(slots=True, kw_only=True)
class UiRecordUtil(DataclassMixin):  # TODO: Move to the appropriate directory
    """Utility type to provide additional functionality for working with records."""

    @classmethod
    def run_get_record_panels(cls, type_name: str, key: str) -> list[RecordPanel]:
        """Get list of record's views."""
        request_type = TypeInfo.from_type_name(type_name)
        if not is_record_type(request_type):
            raise RuntimeError(f"Type {type_name} is not a record type.")
        key_type = request_type.get_key_type()

        # Deserialize the key
        key_obj = _KEY_SERIALIZER.deserialize(key, TypeHint.for_type(key_type))

        # Load the record and update the actual type for correct handlers lookup
        record = active(DataSource).load_one(key_obj)
        actual_type = type(record)

        # Get viewers from TypeDecl
        panels = cls._create_panels_from_handlers(actual_type)

        # Add record's saved views if any
        # TODO (Roman): Currently, loading Views by query does not work for Record types that have key fields
        #  of type 'date'. Fix query serialization so that it works for all supported types.
        try:
            persisted_views = ViewPersistenceUtil.load_all_views_for_record(key_obj)
        except RuntimeError:
            persisted_views = []
        panels += [
            RecordPanel(
                name=pv.view_name,
                label=pv.view_name,
                kind=ViewPersistenceUtil.get_panel_kind_from_view(pv),
                persistable=True
            )
            for pv in persisted_views
        ]

        return panels

    @classmethod
    def _create_panels_from_handlers(cls, type_: type) -> list[RecordPanel]:
        """Create panels from handlers block."""
        handler_block = TypeDecl.for_type(type_).declare
        if not handler_block:
            return []
        return [
            RecordPanel(name=h.name, label=h.label, kind=cls._get_primary_kind_or_none(h), persistable=False)
            for h in handler_block.handlers if cls._is_viewer(h)
        ]

    @classmethod
    def _get_primary_kind_or_none(cls, handler: HandlerDeclareDecl) -> str | None:
        """Get type of the view. If it is a dynamic view with name 'self', return 'Primary', otherwise return None."""
        if cls._is_viewer(handler) and handler.label == "Self":
            return "Primary"
        else:
            return None

    @classmethod
    def _is_viewer(cls, handler: HandlerDeclareDecl) -> bool:
        return handler.type_ == "Viewer"
