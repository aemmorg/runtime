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

import logging
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.tasks.celery.broker.celery_broker import CeleryBroker
from cl.runtime.tasks.task import Task
from cl.runtime.tasks.task_key import TaskKey
from cl.runtime.tasks.task_status import TaskStatus

_logger = logging.getLogger(__name__)


class MongoCeleryBroker(CeleryBroker):
    """Celery broker backed by MongoDB."""

    def resolve_uri(self, uri_template: str | None, env_id: str) -> str:
        """Resolve {env_id} and {context_id} placeholders in the MongoDB broker URI."""
        if not uri_template:
            raise RuntimeError(
                "Celery broker URI is not specified for MongoDB broker. Set 'celery_broker_uri' in settings.yaml."
            )
        if "{" in uri_template:
            return uri_template.format(env_id=env_id, context_id=env_id)
        return uri_template

    def delete_existing_tasks(self, uri: str, queue: str) -> None:
        """Clear all collections in the MongoDB Celery broker database."""
        from pymongo import MongoClient  # noqa

        try:
            all_tasks: tuple[Task, ...] = active(DataSource).load_all(key_type=TaskKey)
            stuck_tasks = [task for task in all_tasks if task.status in (TaskStatus.RUNNING, TaskStatus.PENDING)]

            if stuck_tasks:
                _logger.warning("Deleting %s stuck tasks from previous backend run", len(stuck_tasks))
                active(DataSource).delete_many([task.get_key() for task in stuck_tasks], commit=True)

            mongo_client = MongoClient(uri)
            db_name = uri.split("/")[-1]
            mongo_db = mongo_client[db_name]

            for collection_name in mongo_db.list_collection_names():
                mongo_db.drop_collection(collection_name)

            mongo_client.close()
            _logger.info("Cleared MongoDB Celery broker database: %s", db_name)

        except Exception as e:
            _logger.warning("Failed to clear MongoDB Celery broker: %s", e)
