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
from enum import Enum
from typing import Any
from fastapi import HTTPException
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.protocols import is_primitive_type
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.records.typename import typeof
from cl.runtime.routers.storage.records_with_schema_response import RecordsWithSchemaResponse
from cl.runtime.routers.storage.select_request import SelectRequest
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers

_SELECT_MAX_RECORDS = 10000
"""Hard cap on the number of records returned by /storage/select to prevent unbounded queries."""


class SelectResponse(RecordsWithSchemaResponse):
    """Response data type for the /storage/select route."""

    @classmethod
    def get_response(cls, request: SelectRequest) -> SelectResponse:
        """Implements /storage/select route."""

        if request.query_dict:
            raise HTTPException(status_code=400, detail="Select with 'query_dict' is not supported.")

        if request.table_format is False:
            raise HTTPException(status_code=400, detail="Select with 'table_format=False' is not supported.")

        if request.skip != 0:
            raise HTTPException(status_code=400, detail="Select with 'skip != 0' is not supported.")

        if request.limit is not None:
            raise HTTPException(status_code=400, detail="Select with 'limit' is not supported.")

        ds = active(DataSource)

        # TODO(Roman): !!! Implement separate methods for table and type
        if (type_kind := TypeInfo.get_type_name_info(type_name=request.type_).type_kind) == TypeKind.RECORD:
            # Get records for a type
            record_type_name = request.type_
            record_type = TypeInfo.from_type_name(record_type_name)
            records = ds.load_by_type(record_type)
            common_base_record_type = record_type
        elif type_kind == TypeKind.KEY:
            # Get records for a table
            key_type_name = request.type_
            key_type = TypeInfo.from_type_name(key_type_name)
            records = ds.load_all(key_type)

            if records:
                record_types = [type(record) for record in records]
                common_base_record_type = TypeInfo.get_common_base_type(types=record_types)
            else:
                common_base_record_type = key_type
        else:
            raise RuntimeError(f"Type {request.type_} is neither a record nor a key.")

        # Enforce hard cap to prevent unbounded responses
        records = records[:_SELECT_MAX_RECORDS]

        # Serialize records for table (v2.0.0 shape, no Datatype/Dataset/Database columns)
        serialized_records = [cls._serialize_record_for_table(record) for record in records]

        schema_dict = cls._get_schema_dict(common_base_record_type)

        return SelectResponse(schema_=schema_dict, data=serialized_records)  # noqa

    @classmethod
    def _serialize_record_for_table(cls, record: RecordMixin) -> dict[str, Any]:
        """Serialize record to UI table format: primitives/keys/enums only, plus _t and _key."""

        all_slots = record.get_field_names()

        # Get subset of slots which are supported in table format
        table_fields = {
            CaseUtil.snake_to_pascal_case_keep_trailing_underscore(slot)
            for slot in all_slots
            if (slot_v := getattr(record, slot)) is not None
            and (
                is_primitive_type(typeof(slot_v))
                or is_key_type(type(slot_v))
                or isinstance(slot_v, Enum)
            )
        }

        table_dict = {k: v for k, v in DataSerializers.FOR_UI.serialize(record).items() if k in table_fields}

        table_dict["_t"] = typename(type(record))
        table_dict["_key"] = KeySerializers.DELIMITED.serialize(record.get_key())

        return table_dict
