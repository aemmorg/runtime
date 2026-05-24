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

from urllib.parse import urlparse
from cl.runtime.tasks.celery.broker.celery_broker import CeleryBroker


class RedisCeleryBroker(CeleryBroker):
    """Celery broker backed by Redis."""

    def resolve_uri(self, uri_template: str | None, env_id: str) -> str:
        """Resolve {env_id} and {context_id} placeholders in the Redis broker URI."""
        if not uri_template:
            raise RuntimeError(
                "Celery broker URI is not specified for Redis broker. Set 'celery_broker_uri' in settings.yaml."
            )
        if "{" in uri_template:
            return uri_template.format(env_id=env_id, context_id=env_id)
        return uri_template

    def delete_existing_tasks(self, uri: str, queue: str) -> None:
        """Flush the Redis database used by the Celery broker."""
        import redis

        parsed_uri = urlparse(uri)
        redis_client = redis.StrictRedis(
            host=parsed_uri.hostname, port=parsed_uri.port, db=parsed_uri.path.lstrip("/")
        )
        redis_client.delete(queue)
        redis_client.flushdb()
