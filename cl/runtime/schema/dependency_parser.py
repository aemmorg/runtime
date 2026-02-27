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

from typing import Iterable
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import is_key_or_record_type
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.protocols import is_record_type
from cl.runtime.records.protocols import is_sequence_type
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typeof
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.key_serializers import KeySerializers


class DependencyParser:
    """
    `DependencyParser` is a class that is used for BFS traversal of records` dependency tree
    """

    def __init__(self, records: Iterable[RecordMixin]) -> None:
        """
        Initialize the parser with the record

        Args:
            records: The record to traverse
        """
        records = [record for record in records if record is not None]
        if any(not is_record_type(typeof(record)) for record in records):
            raise ValueError(
                "Input records must implement RecordMixin",
            )

        self.records = records
        self._dependencies: list[RecordMixin] = list(records)
        self.queue: list[RecordMixin | KeyMixin] = list(records)
        self._traversed_items: dict[str, RecordMixin] = {
            KeySerializers.DELIMITED.serialize(record.get_key(), TypeHint.for_type(KeyMixin)): record
            for record in records
        }
        self._is_traversed = False

    def get_dependencies(self, ignore_cache: bool = False) -> Iterable[RecordMixin]:
        """
        Traverse the dependencies of a record recursively and return them

        Args:
            ignore_cache: If True, ignore the cache and re-traverse the dependencies
        """

        if self._is_traversed and not ignore_cache:
            return self._dependencies

        self._dependencies = list(self.records)
        self.queue: list[RecordMixin | KeyMixin] = list(self.records)
        self._traversed_items = {
            KeySerializers.DELIMITED.serialize(record.get_key(), TypeHint.for_type(KeyMixin)): record
            for record in self.records
        }

        self._traverse_dependencies()
        self._is_traversed = True

        return self._dependencies

    def _traverse_dependencies(self) -> None:
        """
        Traverse dependencies from the queue until the queue is empty
        """
        while self.queue:
            item = self.queue.pop(0)
            if item is None or not is_key_or_record_type(typeof(item)):
                continue

            fields = self._get_record_fields(item)
            for field_name, field_value in fields.items():
                if is_sequence_type(type(field_value)):
                    self._process_iterable(field_value)
                    continue

                self._process_item(field_value)

    @staticmethod
    def _get_record_fields(record: RecordMixin) -> dict[str, RecordMixin | KeyMixin | Iterable[RecordMixin | KeyMixin]]:
        # Get slots from this class and its bases in the order of declaration from base to derived
        field_names = record.get_field_names()

        return {
            field_name: field_value
            for field_name in field_names
            if (field_value := getattr(record, field_name)) is not None
        }

    def _process_key(self, key: KeyMixin) -> None:
        serialized_key = KeySerializers.DELIMITED.serialize(key, TypeHint.for_type(KeyMixin))
        if serialized_key in self._traversed_items:
            return

        loaded_record = active(DataSource).load_one_or_none(key)
        self._traversed_items[serialized_key] = loaded_record
        if loaded_record:
            self._dependencies.append(loaded_record)
        # The key might contain dependencies even if the corresponding record doesn't exist, so we need
        # to traverse them as well
        self.queue.append(loaded_record if loaded_record else key)

    def _process_iterable(self, iterable: Iterable) -> None:
        if isinstance(iterable, dict):
            # For each dict value check underlying connections
            iterable = iterable.values()

        iterable = list(iterable)

        if not iterable:
            # Skip processing empty iterables
            return

        for item in iterable:
            if is_sequence_type(type(item)):
                self._process_iterable(item)
                continue

            self._process_item(item)

    def _process_item(self, item: RecordMixin | KeyMixin) -> None:
        if item is None:
            return

        item_type = typeof(item)

        if is_key_type(item_type):
            self._process_key(item)
            return

        if is_record_type(item_type):
            # Embedded records should only be traversed for dependencies, they are not dependencies themselves
            self.queue.append(item)
            return
