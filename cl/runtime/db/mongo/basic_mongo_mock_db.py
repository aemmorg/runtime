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

import uuid
from dataclasses import dataclass
import pymongo
from bson import Binary
from bson.binary import UUID_SUBTYPE
from mongomock import MongoClient as MongoClientMock
from pymongo.synchronous.collection import Collection
from cl.runtime.db.mongo.basic_mongo_db import BasicMongoDb

_bson_uuid_patched = False
"""Flag to ensure the bson UUID patch is applied only once."""


@dataclass(slots=True, kw_only=True)
class BasicMongoMockDb(BasicMongoDb):
    """MongoDB database without bitemporal support using mongomock library for testing."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        self._patch_bson_uuid()

    @staticmethod
    def _patch_bson_uuid() -> None:
        """Patch bson.binary.Binary.from_uuid for mongomock compatibility with UUID fields."""
        global _bson_uuid_patched
        if not _bson_uuid_patched:

            def _patched_from_uuid(uuid_: uuid.UUID, uuid_representation=None):
                return Binary(uuid_.bytes, UUID_SUBTYPE)

            Binary.from_uuid = staticmethod(_patched_from_uuid)
            _bson_uuid_patched = True

    def _get_mongo_client_type(self) -> type:
        """Get the type of MongoDB client object, this method overrides base to return the mongomock class."""
        return MongoClientMock

    def _add_index(
        self,
        *,
        collection: Collection,
        query_type: type,
    ) -> None:
        """Add index for the specified query_type without background parameter for mongomock compatibility."""
        if not self._query_types_with_index:
            # Create an empty set of query types for which the index has already been added
            self._query_types_with_index = set()
        if query_type not in self._query_types_with_index:
            # First fields in the index
            query_index = [("_tenant", pymongo.ASCENDING), ("_dataset", pymongo.ASCENDING)]
            # Populate query fields recursively
            self._populate_index(type_=query_type, result=query_index)
            # Key is the last field in the index
            query_index.append(("_key", pymongo.ASCENDING))

            # Add index to DB without 'background' parameter (mongomock doesn't handle it properly)
            # Convert list to tuple to avoid list/tuple comparison issues
            collection.create_index(tuple(query_index), unique=True)

            # Add to the set of query types for which the index has already been added
            self._query_types_with_index.add(query_type)
