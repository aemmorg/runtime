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

from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from frozendict import frozendict
from cl.runtime.file.file_util import FileUtil
from cl.runtime.file.reader import Reader
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.yaml_encoders import YamlEncoders

_SERIALIZER = DataSerializers.FOR_YAML_DESERIALIZATION
_ENCODER = YamlEncoders.DEFAULT


@dataclass(slots=True, kw_only=True)
class YamlReader(Reader):
    """Load records from YAML files into the context database."""

    def load_file(self, *, file_path: str) -> frozendict[str, tuple[RecordMixin, ...]]:
        """Load records from a single YAML file grouped by dataset."""

        records_by_dataset: dict[str, list[RecordMixin]] = defaultdict(list)
        try:
            record_type = FileUtil.get_type_from_filename(file_path, raise_on_fail=False)

            with open(file_path, mode="r", encoding="utf-8") as file:
                yaml_data = _ENCODER.decode(file.read())

                # Support both single record (dict) and multiple records (list)
                if isinstance(yaml_data, dict):
                    object_dicts = [yaml_data]
                elif isinstance(yaml_data, list):
                    object_dicts = yaml_data
                else:
                    raise RuntimeError("_ENCODER.decode must return a dict or list.")

                invalid_objects = {
                    index
                    for index, object_dict in enumerate(object_dicts)
                    for key in object_dict.keys()
                    if key is None or key == ""
                }

                if invalid_objects:
                    rows_str = "".join([f"Row: {invalid_object}\n" for invalid_object in invalid_objects])
                    raise RuntimeError(
                        "Misaligned values found in the following objects.\n"
                        "Check the placement of colons, dashes and quotes.\n" + rows_str
                    )

                for object_dict in object_dicts:
                    record, dataset = self._deserialize_object(record_type=record_type, object_dict=object_dict)
                    records_by_dataset[dataset or "/"].append(record)
        except Exception as e:
            raise RuntimeError(f"Failed to upload YAML file {file_path}.\n" f"Error: {e}") from e

        return frozendict({k: tuple(v) for k, v in records_by_dataset.items()})

    @classmethod
    def _deserialize_object(
        cls, *, record_type: type | None, object_dict: dict[str, Any]
    ) -> tuple[RecordMixin, str | None]:
        """Deserialize YAML object into a record with optional dataset.
        Args:
            record_type: Record type hint derived from filename, or None if not available.
            object_dict: Dictionary representing the YAML object.
        Returns:
            Tuple of (deserialized record, dataset string or None).
        Raises:
            RuntimeError: If record type cannot be determined or deserialization fails.
        """

        # First, check if _type is provided in the YAML object
        # If _type is provided and valid, use it and ignore record_type from filename.
        if "_type" in object_dict:
            record_type_name = object_dict["_type"]

            # Get the actual record type from _type field
            try:
                record_type = TypeInfo.from_type_name(record_type_name)
            except Exception as e:
                # _type provided but invalid
                raise RuntimeError(
                    f"Could not determine record type '{record_type_name}'from YAML '_type'. Provide a valid type.\n"
                    f"Error: {e}"
                )

        # If record_type is still None, we cannot determine the type
        if record_type is None:
            raise RuntimeError(
                "Could not determine record type: "
                "YAML '_type' is missing/invalid and filename-derived type not available."
            )

        # Extract _dataset before deserialization (not a record field)
        dataset = object_dict.pop("_dataset", None)

        # Ensure _type is set for deserialization
        object_dict["_type"] = typename(record_type)

        result = _SERIALIZER.deserialize(object_dict).build()
        return result, dataset
