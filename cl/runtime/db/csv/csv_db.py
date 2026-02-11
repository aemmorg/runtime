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

import csv
import os
import shutil
from dataclasses import dataclass
from typing import Sequence
from cl.runtime.db.db import Db
from cl.runtime.db.query_mixin import QueryMixin
from cl.runtime.db.save_policy import SavePolicy
from cl.runtime.db.sort_order import SortOrder
from cl.runtime.primitive.char_util import CharUtil
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.record_mixin import TRecord
from cl.runtime.records.type_check import TypeCheck
from cl.runtime.records.typename import typename
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers

_DATA_SERIALIZER = DataSerializers.FOR_CSV
"""Serializer for CSV data serialization and deserialization."""

_KEY_SERIALIZER = KeySerializers.TUPLE
"""Serializer for keys used in deduplication and lookup."""


@dataclass(slots=True, kw_only=True)
class CsvDb(Db):
    """Db implementation that stores records as append-only CSV files."""

    csv_dir: str | None = None
    """Directory where CSV files are stored, defaults to {project_root}/records."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Default csv_dir to {project_root}/records
        if self.csv_dir is None:
            from cl.runtime.project.project_layout import ProjectLayout

            self.csv_dir = os.path.join(ProjectLayout.get_project_root(), "records")
        elif not os.path.isabs(self.csv_dir):
            from cl.runtime.project.project_layout import ProjectLayout

            self.csv_dir = os.path.join(ProjectLayout.get_project_root(), self.csv_dir)

    def is_empty(self) -> bool:
        """Return true if no CSV files exist in csv_dir."""
        if not os.path.exists(self.csv_dir):
            return True
        csv_files = [f for f in os.listdir(self.csv_dir) if f.endswith(".csv")]
        return len(csv_files) == 0

    def load_many(
        self,
        key_type: type[KeyMixin],
        keys: Sequence[KeyMixin],
        *,
        dataset: str,
        tenant: str,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder,
    ) -> tuple[RecordMixin, ...]:

        # Check params
        assert TypeCheck.guard_key_type(key_type)
        assert TypeCheck.guard_key_sequence(keys)
        self._check_dataset(dataset)
        self._check_tenant(tenant)

        # Load all records then filter by requested keys
        all_records = self._load_all(key_type, dataset=dataset, tenant=tenant, sort_order=sort_order)
        requested_keys = set(_KEY_SERIALIZER.serialize(k) for k in keys)
        return tuple(r for r in all_records if _KEY_SERIALIZER.serialize(r.get_key()) in requested_keys)

    def load_all(
        self,
        key_type: type[KeyMixin],
        *,
        dataset: str,
        tenant: str,
        cast_to: type[TRecord] | None = None,
        restrict_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder = SortOrder.ASC,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:

        # Check params
        assert TypeCheck.guard_key_type(key_type)
        self._check_dataset(dataset)
        self._check_tenant(tenant)

        csv_file_path = self._get_csv_file_path(key_type)
        if not os.path.exists(csv_file_path):
            return tuple()

        base_type_name = typename(key_type).removesuffix("Key")

        # Read CSV and deduplicate by key (last-key-wins)
        records_by_key = {}
        with open(csv_file_path, mode="r", encoding="utf-8") as file:
            csv_reader = csv.DictReader(file)
            for row_dict in csv_reader:
                # Normalize characters and convert empty strings to None
                row_dict = {CharUtil.normalize(k): CharUtil.normalize_or_none(v) for k, v in row_dict.items()}

                # Set _type from the CSV column if absent or empty, default to base type name
                if row_dict.get("_type") is None:
                    row_dict["_type"] = base_type_name

                # Deserialize and build the record
                record = _DATA_SERIALIZER.deserialize(row_dict).build()
                record_key = _KEY_SERIALIZER.serialize(record.get_key())
                records_by_key[record_key] = record

        records = list(records_by_key.values())

        # Apply restrict_to filter
        if restrict_to is not None:
            records = [r for r in records if isinstance(r, restrict_to)]

        # Apply sort
        if sort_order == SortOrder.DESC:
            records.sort(key=lambda r: _KEY_SERIALIZER.serialize(r.get_key()), reverse=True)
        else:
            records.sort(key=lambda r: _KEY_SERIALIZER.serialize(r.get_key()))

        # Apply skip and limit
        if skip is not None and skip > 0:
            records = records[skip:]
        if limit is not None:
            records = records[:limit]

        return tuple(records)

    def load_by_query(
        self,
        query: QueryMixin,
        *,
        dataset: str,
        tenant: str,
        cast_to: type[TRecord] | None = None,
        restrict_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder = SortOrder.ASC,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        raise NotImplementedError(f"{typename(type(self))} does not support load_by_query.")

    def count_by_query(
        self,
        query: QueryMixin,
        *,
        dataset: str,
        tenant: str,
        restrict_to: type | None = None,
    ) -> int:
        raise NotImplementedError(f"{typename(type(self))} does not support count_by_query.")

    def save_many(
        self,
        key_type: type[KeyMixin],
        records: Sequence[RecordMixin],
        *,
        dataset: str,
        tenant: str,
        save_policy: SavePolicy,
    ) -> None:

        # Check params
        assert TypeCheck.guard_key_type(key_type)
        assert TypeCheck.guard_record_sequence(records)
        self._check_dataset(dataset)
        self._check_tenant(tenant)

        if not records:
            return

        csv_file_path = self._get_csv_file_path(key_type)

        # Serialize all records
        serialized_records = []
        for record in records:
            serialized_record = dict(_DATA_SERIALIZER.serialize(record))
            # Ensure _type is always present
            if "_type" not in serialized_record:
                serialized_record["_type"] = typename(type(record))
            serialized_records.append(serialized_record)

        # Determine fieldnames: _type first, then remaining columns sorted
        all_columns = set()
        for sr in serialized_records:
            all_columns.update(sr.keys())
        all_columns.discard("_type")
        fieldnames = ["_type"] + sorted(all_columns)

        # If file exists, read existing header and merge
        file_exists = os.path.exists(csv_file_path)
        if file_exists:
            with open(csv_file_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                existing_header = next(reader, None)
            if existing_header:
                existing_set = set(existing_header)
                new_columns = [c for c in fieldnames if c not in existing_set]
                fieldnames = existing_header + new_columns
                # Rewrite file with updated header if new columns were added
                if new_columns:
                    self._rewrite_csv_with_new_header(csv_file_path, fieldnames)

        # Ensure directory exists
        os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)

        # Append records to CSV file
        write_header = not file_exists
        with open(csv_file_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if write_header:
                writer.writeheader()
            for sr in serialized_records:
                writer.writerow(sr)

    def delete_many(
        self,
        key_type: type[KeyMixin],
        keys: Sequence[KeyMixin],
        *,
        dataset: str,
        tenant: str,
    ) -> None:
        raise NotImplementedError(f"{typename(type(self))} does not support delete_many.")

    def delete_by_query(
        self,
        query: QueryMixin,
        *,
        dataset: str,
        tenant: str,
        restrict_to: type | None = None,
    ) -> None:
        raise NotImplementedError(f"{typename(type(self))} does not support delete_by_query.")

    def close_connection(self) -> None:
        """No connections to close for file-based storage."""
        pass  # TODO: Close file connection in this case

    def _drop_db_do_not_call_directly(self) -> None:
        """DO NOT CALL DIRECTLY, call drop_db() instead."""
        # Remove CSV directory
        if self.csv_dir and os.path.exists(self.csv_dir):
            shutil.rmtree(self.csv_dir)

    def _get_csv_file_path(self, key_type: type[KeyMixin]) -> str:
        """Get the CSV file path for the given key type."""
        table_name = typename(key_type).removesuffix("Key")
        return os.path.join(self.csv_dir, f"{table_name}.csv")

    @staticmethod
    def _rewrite_csv_with_new_header(csv_file_path: str, new_fieldnames: list[str]) -> None:
        """Rewrite CSV file with an updated header for column evolution."""
        with open(csv_file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        with open(csv_file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=new_fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
