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
from typing import Any
from pydantic import BaseModel
from pydantic import ConfigDict
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.routers.task.result_request import ResultRequest
from cl.runtime.routers.task.status_response_item import LEGACY_TASK_STATUS_NAMES_MAP
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.tasks.instance_method_task import InstanceMethodTask
from cl.runtime.tasks.task import Task
from cl.runtime.tasks.task_key import TaskKey


class ResultResponseItem(BaseModel):
    """Response data type for the /tasks/result route."""

    task_run_id: str
    """Task run id."""

    key: str | None = None
    """Key string in semicolon-delimited format."""

    result: Any
    """Task result (mapped status name, or error message on failure)."""

    model_config = ConfigDict(alias_generator=CaseUtil.snake_to_pascal_case, populate_by_name=True)

    @classmethod
    def get_response(cls, request: ResultRequest) -> list[ResultResponseItem]:
        """Get results for tasks in request."""

        task_keys = [TaskKey(task_id=x).build() for x in request.task_run_ids]
        tasks = active(DataSource).load_many(task_keys, cast_to=Task)

        response_items = []
        for task in tasks:
            # Use record key for InstanceMethodTask, None otherwise
            if isinstance(task, InstanceMethodTask):
                key = KeySerializers.DELIMITED.serialize(task.key)
            else:
                key = None

            # Use error_message for failed tasks, mapped status name otherwise
            result = (
                task.error_message
                if task.error_message
                else LEGACY_TASK_STATUS_NAMES_MAP.get(task.status.name, task.status.name)
            )

            response_items.append(
                ResultResponseItem(
                    result=result,
                    task_run_id=str(task.task_id),
                    key=key,
                ),
            )

        return response_items
