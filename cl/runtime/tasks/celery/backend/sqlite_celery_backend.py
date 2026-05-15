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
from cl.runtime.tasks.celery.backend.celery_backend import CeleryBackend


class SqliteCeleryBackend(CeleryBackend):
    """Celery result backend backed by a SQLite database."""

    def resolve_uri(self, uri_template: str | None, env_id: str) -> str:
        """Resolve the backend URI, building a default SQLite path when the template is absent or unresolved."""
        if uri_template is not None and "{" not in uri_template:
            return uri_template

        from cl.runtime.project.resources_util import ResourcesUtil

        celery_root = ResourcesUtil.get_celery_root()
        os.makedirs(celery_root, exist_ok=True)
        backend_file = os.path.join(celery_root, f"celery-backend.{env_id.lower()}.sqlite")
        return f"db+sqlite:///{backend_file}"
