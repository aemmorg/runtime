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

from __future__ import annotations
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.protocols import is_mixin_type
from cl.runtime.routers.storage.load_request import LoadRequest
from cl.runtime.routers.storage.records_with_schema_response import RecordsWithSchemaResponse
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.ui.ui_type_state import UiTypeState
from cl.runtime.ui.ui_type_state_key import UiTypeStateKey

_KEY_SERIALIZER = KeySerializers.DELIMITED
_UI_SERIALIZER = DataSerializers.FOR_UI


class LoadResponse(RecordsWithSchemaResponse):
    """Response data type for the /storage/load route."""

    @classmethod
    def get_response(cls, request: LoadRequest) -> LoadResponse:
        # TODO: !!! Consider returning the same size of result as the input

        # Handle empty request
        if not request.load_keys:
            return LoadResponse(schema_=cls._get_schema_dict(None), data=[])  # noqa

        # TODO: !!! Do not rely on first element to detect type
        record_type_name = request.load_keys[0].type
        record_type = TypeInfo.from_type_name(record_type_name)
        if is_mixin_type(record_type):
            # If record type is mixin, use it directly for deserialization
            key_type = record_type
        else:
            key_type = record_type.get_key_type()

        # Deserialize keys in request
        keys = tuple(
            _KEY_SERIALIZER.deserialize(x.key, TypeHint.for_type(key_type)).build()
            for x in request.load_keys or tuple()
        )

        # Load records and drop None entries
        loaded_records = active(DataSource).load_many_or_none(keys)
        loaded_records = [r for r in loaded_records if r is not None]

        if not loaded_records:
            return LoadResponse(schema_=cls._get_schema_dict(None), data=[])  # noqa

        # Find the lowest common base of the loaded types
        loaded_record_types = tuple(type(x) for x in loaded_records)
        common_base = TypeInfo.get_common_base_type(types=loaded_record_types)

        # Serialize records for UI (v2.0.0 shape, no Datatype/Dataset/Database columns)
        serialized_records = [_UI_SERIALIZER.serialize(record) for record in loaded_records]

        # Create schema dict for the common base
        schema_dict = cls._get_schema_dict(common_base)

        return LoadResponse(schema_=schema_dict, data=serialized_records)  # noqa

    @classmethod
    def _get_default_ui_type_state(cls, ui_type_state_requested_key: UiTypeStateKey) -> UiTypeState:
        """Return default UiTypeState with all discovered handler names pinned.

        Uses DataSpec.handlers (v2.0.0) rather than the legacy TypeDecl path.
        """
        from cl.runtime.schema.type_info import TypeInfo as _TI
        type_state_record_type = _TI.from_type_name(ui_type_state_requested_key.type_.name)
        spec = type_state_record_type.get_type_spec()

        all_handlers: list[str] = []
        handlers = getattr(spec, "handlers", None) or []
        for h in handlers:
            if h.name not in all_handlers:
                all_handlers.append(h.name)

        return UiTypeState(
            user=ui_type_state_requested_key.user,
            type_=ui_type_state_requested_key.type_,
            pinned_handlers=all_handlers,
        )
