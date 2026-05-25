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
from typing import cast
from inflection import titleize
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.for_pydantic.pydantic_mixin import PydanticMixin
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.records.typename import typenameof
from cl.runtime.routers.schema.type_request import TypeRequest
from cl.runtime.routers.schema.type_response import TypeResponse
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.services.data.data_envs_response import DataEnvsResponse
from cl.runtime.services.data.load_record_response import LoadRecordResponse
from cl.runtime.services.data.screens_response import ScreensResponse
from cl.runtime.services.data.select_data_response import SelectDataResponse
from cl.runtime.services.data.table_screen_item import TableScreenItem
from cl.runtime.services.data.type_screen_item import TypeScreenItem

# Create serializers
_UI_SERIALIZER = DataSerializers.FOR_UI
_KEY_SERIALIZER = KeySerializers.DELIMITED


class DataService(PydanticMixin):
    """Service class for data-related actions."""

    @classmethod
    def run_screens(cls) -> ScreensResponse:
        """Return data about screens that can be opened according to records in DB."""

        ds = active(DataSource)

        # Build 'tables' as a list of key types stored in db
        tables = [
            TableScreenItem(
                table_name=(key_type_name := typename(key_type)),
                label=titleize(key_type_name).removesuffix(" Key"),
            )
            for key_type in ds.get_key_types()
        ]

        # Build 'types' as a list of record types stored in db
        types = [
            TypeScreenItem(
                type_name=(record_type_name := typename(record_type)),
                table_name=typename(TypeInfo.from_type_name(record_type_name).get_key_type()),
                label=titleize(record_type_name),
            )
            for record_type in ds.get_record_types()
        ]

        # TODO (Roman): Implement 'filters' collection
        # Build 'filters' as a list of queries stored in db
        filters = []

        screens = ScreensResponse(
            tables=tables,
            types=types,
            filters=filters,
        )

        return screens

    @classmethod
    def run_select_table(
        cls,
        table_name: str,
        skip: int | None = None,
        limit: int | None = None,
        query_dict: Any | None = None,
    ) -> SelectDataResponse:
        """Select records by table from DB. `query_dict` accepted for v2.0.0 signature but currently ignored."""

        ds: DataSource = active(DataSource)

        # Select by table using load_all
        type_ = cast(type[KeyMixin], TypeInfo.from_type_name(table_name))
        records = ds.load_all(type_, skip=skip, limit=limit)

        if records:
            # Get the common type of the records stored in the table
            record_types = [type(record) for record in records]
            common_base_record_type = TypeInfo.get_common_base_type(types=record_types)
        else:
            # Default to type_ when there are no records
            common_base_record_type = type_

        # Serialize records in UI format and add '_key' attribute
        data = [{**_UI_SERIALIZER.serialize(x), "_key": _KEY_SERIALIZER.serialize(x.get_key())} for x in records]

        # Get type spec + dependencies via v2.0.0 TypeResponse
        schema_response = TypeResponse.get_type(
            TypeRequest(type_name=typename(common_base_record_type)),
            include_fields=False,
        )

        return SelectDataResponse(
            data=data,
            type_spec=schema_response.type_spec,
            dependencies=schema_response.dependencies,
            query_schemas=None,
        )

    @classmethod
    def run_select_type(
        cls,
        type_name: str,
        skip: int | None = None,
        limit: int | None = None,
        query_dict: Any | None = None,
    ) -> SelectDataResponse:
        """Select records by type from DB. `query_dict` accepted for v2.0.0 signature but currently ignored."""

        ds: DataSource = active(DataSource)

        # Select by type
        type_ = cast(type[RecordMixin], TypeInfo.from_type_name(type_name))
        records = ds.load_by_type(type_, skip=skip, limit=limit)

        # Serialize records in UI format and add '_key' attribute
        data = [{**_UI_SERIALIZER.serialize(x), "_key": _KEY_SERIALIZER.serialize(x.get_key())} for x in records]

        # Get type spec + dependencies via v2.0.0 TypeResponse
        schema_response = TypeResponse.get_type(
            TypeRequest(type_name=typename(type_)),
            include_fields=False,
        )

        return SelectDataResponse(
            data=data,
            type_spec=schema_response.type_spec,
            dependencies=schema_response.dependencies,
            query_schemas=None,
        )

    @classmethod
    def run_select_filter(cls, table_name: str, filter_name: str):
        """Select records by filter from DB."""

        raise NotImplementedError("Select by filter currently is not supported.")

    @classmethod
    def run_data_envs(cls) -> DataEnvsResponse:
        """Return the data environment hierarchy.

        Contract-stub: this build has no DataEnv records, so the response always carries an
        empty `data_env_items` list and a null `default_env`. The FE renders the dropdown as
        empty and skips the active-env switching.
        """
        return DataEnvsResponse(data_env_items=[], default_env=None)

    @classmethod
    def run_set_active_data_env(cls, env_name: str) -> None:
        """Set the active data environment.

        Contract-stub: no DataEnv records exist, so this is a no-op accepted from the FE.
        """

    @classmethod
    def run_load_record(cls, type_name: str, key: str) -> LoadRecordResponse:
        """Load a single record by type name and serialized key string."""
        ds: DataSource = active(DataSource)

        # Resolve key type from type_name and deserialize key string
        type_ = cast(type[KeyMixin], TypeInfo.from_type_name(type_name))
        key_type = type_.get_key_type()
        key_obj = _KEY_SERIALIZER.deserialize(key, type_hint=TypeHint.for_type(key_type)).build()

        # Load record from DB (returns None if not found)
        record = ds.load_one_or_none(key_obj)

        if record is None:
            return LoadRecordResponse()

        # Serialize record for UI
        data = _UI_SERIALIZER.serialize(record)

        # Get type spec and dependencies in the v2.0.0 response shape
        schema_response = TypeResponse.get_type(TypeRequest(type_name=typenameof(record)))

        return LoadRecordResponse(
            record=data,
            type_spec=schema_response.type_spec,
            dependencies=schema_response.dependencies,
        )
