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


class RabbitmqCeleryBroker(CeleryBroker):
    """Celery broker backed by RabbitMQ."""

    def resolve_uri(self, uri_template: str | None, env_id: str) -> str:
        """Resolve {env_id} and {context_id} placeholders in the RabbitMQ broker URI."""
        if not uri_template:
            raise RuntimeError(
                "Celery broker URI is not specified for RabbitMQ broker. Set 'celery_broker_uri' in settings.yaml."
            )
        if "{" in uri_template:
            return uri_template.format(env_id=env_id, context_id=env_id)
        return uri_template

    def delete_existing_tasks(self, uri: str, queue: str) -> None:
        """Purge all messages from the RabbitMQ queue."""
        import pika
        from pika.exceptions import ChannelClosedByBroker

        parsed_uri = urlparse(uri)
        user, password = parsed_uri.netloc.split("@")[0].split(":")

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=parsed_uri.hostname,
                port=parsed_uri.port,
                credentials=pika.PlainCredentials(user, password),
            )
        )
        channel = connection.channel()

        try:
            channel.queue_declare(queue=queue, passive=True)
            channel.queue_purge(queue=queue)
        except ChannelClosedByBroker:
            pass
        finally:
            connection.close()
