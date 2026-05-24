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

import os
from cl.runtime.project.resources_util import ResourcesUtil
from cl.runtime.tasks.celery.broker.celery_broker import CeleryBroker


class SqliteCeleryBroker(CeleryBroker):
    """Celery broker backed by a SQLite database via SQLAlchemy transport."""

    def resolve_uri(self, uri_template: str | None, env_id: str) -> str:
        """Resolve the broker URI, building a default SQLite path when the template is absent or unresolved."""
        if uri_template is not None and "{" not in uri_template:
            return uri_template

        celery_root = ResourcesUtil.get_celery_root()
        os.makedirs(celery_root, exist_ok=True)
        celery_file = os.path.join(celery_root, f"celery.{env_id.lower()}.sqlite")
        return f"sqlalchemy+sqlite:///{celery_file}"

    def delete_existing_tasks(self, uri: str, queue: str) -> None:
        """Remove the SQLite broker database file."""
        celery_file = uri.split("sqlite:///")[1]
        if os.path.exists(celery_file):
            os.remove(celery_file)
