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

from dataclasses import dataclass
from typing import final
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.settings.env_settings import EnvSettings
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class CelerySettings(Settings):
    """Celery settings."""

    celery_is_embedded_worker: bool = True
    """Flag that indicates whether the Celery worker runs embedded within the backend process."""

    celery_broker_type: str = required()
    """Celery broker class name (e.g. SqliteCeleryBroker, MongoCeleryBroker). Must be set in settings.yaml."""

    celery_broker_uri: str | None = None
    """Celery broker URI template. Supports {env_id} placeholder for per-instance isolation."""

    celery_broker_queue: str = "celery-{env_id}"
    """Celery broker queue name. Supports {env_id} placeholder for per-instance isolation."""

    celery_backend_type: str | None = None
    """Celery result backend class name (e.g. SqliteCeleryBackend, MongoCeleryBackend). Optional."""

    celery_backend_uri: str | None = None
    """Celery result backend URI template. Supports {env_id} placeholder for per-instance isolation."""

    celery_workers: int = 2
    """Maximum number of workers for Celery."""

    celery_max_retries: int = 0
    """Maximum number of retries for Celery tasks."""

    celery_time_limit: int = 3600 * 2
    """Time limit for Celery tasks in seconds."""

    celery_pool_type: str = "solo"
    """Pool type for Celery workers."""

    celery_max_tenant_tasks: int = 10
    """Maximum number of tenant tasks at the same time."""

    celery_multiprocess_pool: bool = True
    """Use multiple worker processes instead of single embedded worker (Windows optimization)."""

    celery_worker_restart_interval: int = 60
    """Interval in seconds to check and restart dead workers."""

    celery_worker_log_level: str = "info"
    """Log level for worker processes."""

    celery_worker_optimization: bool = True
    """Enable Windows-specific optimizations (no gossip, mingle, heartbeat)."""

    celery_resume_on_launch: bool | None = None
    """If True, resume execution of tasks remaining in the celery queue from a previous process.
    If None or False (default), wipe the celery DB on launch so stale tasks do not execute."""

    def __init(self) -> None:
        if not self.celery_broker_type:
            raise RuntimeError(
                "Celery broker type is not specified in settings. Set 'celery_broker_type' in settings.yaml."
            )

        env_id = EnvSettings.instance().env_id

        from cl.runtime.tasks.celery.broker.celery_broker import CeleryBroker

        broker = CeleryBroker.create(self.celery_broker_type)
        self.celery_broker_uri = broker.resolve_uri(self.celery_broker_uri, env_id)

        template_vars = {"env_id": env_id, "context_id": env_id}
        if self.celery_broker_queue and "{" in self.celery_broker_queue:
            self.celery_broker_queue = self.celery_broker_queue.format(**template_vars)
        if not self.celery_broker_queue:
            self.celery_broker_queue = f"celery-{env_id.lower()}"

        if self.celery_backend_type:
            from cl.runtime.tasks.celery.backend.celery_backend import CeleryBackend

            backend = CeleryBackend.create(self.celery_backend_type)
            self.celery_backend_uri = backend.resolve_uri(self.celery_backend_uri, env_id)
