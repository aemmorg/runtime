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

from cl.runtime.tasks.celery.backend.celery_backend import CeleryBackend


class MongoCeleryBackend(CeleryBackend):
    """Celery result backend backed by MongoDB."""

    def resolve_uri(self, uri_template: str | None, env_id: str) -> str:
        """Resolve {env_id} and {context_id} placeholders in the MongoDB backend URI."""
        if not uri_template:
            raise RuntimeError(
                "Celery backend URI is not specified for MongoDB backend. " "Set 'celery_backend_uri' in settings.yaml."
            )
        if "{" in uri_template:
            return uri_template.format(env_id=env_id, context_id=env_id)
        return uri_template
