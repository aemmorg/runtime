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
from typing import cast
from pydantic import BaseModel
from pydantic import ConfigDict
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.dataset_key import DatasetKey
from cl.runtime.db.dataset_util import DatasetUtil
from cl.runtime.db.db import Db
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.routers.storage.datasets_request import DatasetsRequest
from cl.runtime.schema.type_info import TypeInfo


class DatasetsResponseItem(BaseModel):
    """Response data type for the /storage/datasets route."""

    name: str | None
    """Name of the dataset."""

    parent: str | None = None
    """Name of the parent dataset."""

    model_config = ConfigDict(alias_generator=CaseUtil.snake_to_pascal_case, populate_by_name=True)

    @classmethod
    def get_datasets(cls, request: DatasetsRequest) -> list[DatasetsResponseItem]:
        """Implements /storage/datasets route."""

        ds = active(DataSource)
        db = cast(Db, ds.db)
        tenant = ds.tenant.tenant_id

        # Resolve key type from the type name in the request
        record_type = TypeInfo.from_type_name(request.type_name)
        key_type = record_type.get_key_type()

        # Query the database for distinct datasets stored for this key type
        actual_datasets = db.get_datasets(key_type, tenant=tenant)

        # Query datasets declared using Dataset record class
        declared_datasets = [dataset.dataset_id for dataset in ds.load_all(DatasetKey)]

        # Merge actual and declared datasets
        datasets = set(actual_datasets + declared_datasets)

        # Expand to include all intermediate levels (e.g. /am/abc adds /am and root)
        all_datasets = set()
        for dataset in datasets:
            all_datasets.update(DatasetUtil.to_lookup_list(dataset))

        # Build response items with parent relationships derived from dataset paths
        result = []
        for dataset in all_datasets:
            levels = DatasetUtil.to_levels(dataset)
            if not levels:
                # Root dataset has no parent
                parent = None
            else:
                # Parent is one level up
                parent = DatasetUtil.combine(*levels[:-1])
            result.append(DatasetsResponseItem(name=dataset, parent=parent))

        result.sort(key=lambda item: item.name or "")
        return result
