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

from typing import cast
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.record_type_presence import RecordTypePresence
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_info import TypeInfo


class DataSourceUtil:
    """Utility class for navigating the DataSource parent chain."""

    @classmethod
    def get_parent_chain(cls, data_source: DataSource) -> list[DataSource]:
        """
        Return the parent chain as a list starting from data_source and ending at the root.

        The result is memoized on the DataSource instance in _parent_chain_cache.

        Args:
            data_source: The DataSource instance to start from.
        """

        # Return cached result if available
        if data_source._parent_chain_cache is not None:
            return data_source._parent_chain_cache

        # Build the chain by walking up the parent links
        chain = []
        current = data_source
        visited = set()
        while current is not None:
            # Guard against cycles
            current_id = id(current)
            if current_id in visited:
                break
            visited.add(current_id)
            chain.append(current)
            current = cast(DataSource, current.parent) if current.parent is not None else None

        # Cache on the instance
        data_source._parent_chain_cache = chain
        return chain

    @classmethod
    def has_multiple_datasets(cls, data_source: DataSource, *, record_type: type[RecordMixin]) -> bool:
        """
        Return True if the database contains records of the specified type in more than one dataset.

        Uses RecordTypePresence records to determine distinct datasets without querying actual data tables.

        Args:
            data_source: The active DataSource instance.
            record_type: Record type to check (uses this type and its subtypes).
        """
        presences = data_source.load_by_type(RecordTypePresence)
        matching_type_names = set(TypeInfo.get_child_and_self_type_names(record_type))
        distinct_datasets = {p.dataset for p in presences if typename(p.record_type) in matching_type_names}
        return len(distinct_datasets) > 1

    @classmethod
    def has_multiple_databases(cls, data_source: DataSource) -> bool:
        """
        Return True if the parent chain has more than one unique database.

        Args:
            data_source: The active DataSource instance.
        """
        chain = cls.get_parent_chain(data_source)
        return len({ds.db.db_id for ds in chain}) > 1
