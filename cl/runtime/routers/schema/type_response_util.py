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
from cl.runtime.contexts.context_manager import active_or_none
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.data_source_util import DataSourceUtil
from cl.runtime.records.typename import typename
from cl.runtime.routers.schema.type_request import TypeRequest
from cl.runtime.schema.module_decl_key import ModuleDeclKey
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_info import TypeInfo


class TypeResponseUtil:
    """Response helper class for the /schema/typeV2 route."""

    @classmethod
    def has_descendant_types(cls, record_type: type) -> bool:
        """Check if RecordTypePresence has entries for any descendant of the given type."""
        descendant_names = set(TypeInfo.get_child_type_names(record_type))
        if not descendant_names:
            return False
        ds = active(DataSource)
        present_record_types = ds.get_record_types(key_type=record_type.get_key_type())
        present_type_names = {typename(x) for x in present_record_types}
        return bool(descendant_names & present_type_names)

    @classmethod
    def get_type(cls, request: TypeRequest) -> dict[str, dict]:
        """Supports /schema/type route."""

        # TODO(Roman): !!! Implement separate methods for table and type
        if TypeInfo.is_known_type_name(request.type_name):
            # TODO: Check why empty module is passed, is module the short name prefix?
            record_type_name = request.type_name
            record_type = TypeInfo.from_type_name(record_type_name)
        else:
            # Get the common type of the records stored in the table, or the table's key type if it is empty
            key_type = TypeInfo.from_type_name(request.type_name)
            record_type = active(DataSource).get_common_base_record_type(key_type=key_type)

        handler_args_elements = dict()
        result = TypeDecl.as_dict_with_dependencies(record_type)

        # Find an element in the results for a record type to use as the basis for a synthetic table item
        record_type_key_in_result = f"{ModuleDeclKey().build().module_name}.{typename(record_type)}"
        record_type_result = result.get(record_type_key_in_result)

        # Add a synthetic Datatype element to the schema only if descendant types exist in DB
        if record_type_result is not None and cls.has_descendant_types(record_type):
            elements = record_type_result.get("Elements", None)
            if elements is not None and not any(e.get("Name") == "Datatype" for e in elements):
                datatype_element = {
                    "Value": {"Type": "String"},
                    "Name": "Datatype",
                    "Comment": "Record class name.",
                    "ReadOnly": True,
                }
                elements.insert(0, datatype_element)

        # Add synthetic Dataset and Database elements if the parent chain has multiple values
        ds = active_or_none(DataSource)
        if record_type_result is not None and ds is not None:
            include_dataset = DataSourceUtil.has_multiple_datasets(ds, record_type=record_type)
            include_database = DataSourceUtil.has_multiple_databases(ds)
        else:
            include_dataset = False
            include_database = False
        if record_type_result is not None and (include_dataset or include_database):
            elements = record_type_result.get("Elements", None)
            if elements is not None:
                # Insert after Datatype if present, otherwise at position 0
                insert_idx = 1 if any(e.get("Name") == "Datatype" for e in elements) else 0
                # Insert Database first, then Dataset at the same index so Dataset ends up before Database
                if include_database and not any(e.get("Name") == "Database" for e in elements):
                    elements.insert(insert_idx, {
                        "Value": {"Type": "String"},
                        "Name": "Database",
                        "Comment": "Database identifier.",
                        "ReadOnly": True,
                    })
                if include_dataset and not any(e.get("Name") == "Dataset" for e in elements):
                    elements.insert(insert_idx, {
                        "Value": {"Type": "String"},
                        "Name": "Dataset",
                        "Comment": "Dataset of the data source.",
                        "ReadOnly": True,
                    })

        # Add synthetic table item to schema
        table_type_key_in_result = f"{ModuleDeclKey().build().module_name}.{request.type_name}"
        table_type_result = {k: v for k, v in record_type_result.items()}
        table_type_result["Name"] = request.type_name
        result[table_type_key_in_result] = table_type_result

        # TODO: Experimental patch to exclude generated fields from top grid and editor but not the record picker
        # This patch is activated in three cases:
        # - Top grid
        # - When a new record is created and the editor is opened
        # - When getting the schema for the picker, however this is excluded by endswith("Key")
        if request.type_name is not None and not request.type_name.endswith("Key"):
            type_dict = list(result.values())[0] if len(result) > 0 else None
            if type_dict is not None:
                elements = type_dict.get("Elements", None)
                if elements is not None:
                    for index, element in enumerate(elements):
                        if element.get("Name", None) in ["EntryId", "CompletionId"]:  # TODO: Replace by preloads
                            elements.pop(index)
                            break

        for decl_name, decl_dict in result.items():
            # Add Implement handlers block
            if not (declare_block := decl_dict.get("Declare")):
                continue

            if not (handlers_block := declare_block.get("Handlers")):
                continue

            # TODO (Roman): Skip abstract methods
            implement_block = [{"Name": handler_decl.get("Name")} for handler_decl in handlers_block]
            result[decl_name]["Implement"] = {"Handlers": implement_block}

            # Create schema for method arguments if so present
            for handler in handlers_block:
                if not (params := handler.get("Params")):
                    continue

                handler_args_schema_name = f"{decl_name}{handler['Name']}Args"
                handler_args_elements[handler_args_schema_name] = {"Elements": params}

        result.update(handler_args_elements)
        return result
