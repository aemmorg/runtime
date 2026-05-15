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
from dataclasses import dataclass
from typing import final
from cl.runtime.project.resources_util import ResourcesUtil
from cl.runtime.settings.env_settings import EnvSettings
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class CelerySettings(Settings):
    """Celery settings."""

    celery_is_embedded_worker: bool = True
    """Flag that indicates whether the Celery worker runs embedded within the backend process."""

    celery_broker: str = "sqlite"
    """Celery broker to be used."""

    celery_broker_uri: str = "sqlalchemy+sqlite:///{project_dir}/celery-{context_id}.db"
    """Celery broker URI. The value from config file is ignored for `sqlite` broker."""

    celery_broker_queue: str = "celery"
    """Celery broker queue."""

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
        if not self.celery_broker:
            raise RuntimeError("Celery broker is not specified in settings.")

        if self.celery_broker == "sqlite":
            celery_root = ResourcesUtil.get_celery_root()
            env_id = EnvSettings.instance().env_id
            celery_file = os.path.join(celery_root, f"celery.{env_id.lower()}.sqlite")

            os.makedirs(celery_root, exist_ok=True)

            self.celery_broker_uri = f"sqlalchemy+sqlite:///{celery_file}"
        elif self.celery_broker in ["redis", "rabbitmq", "sqs", "mongodb"]:
            if not self.celery_broker_uri:
                raise RuntimeError("Celery broker URI is not specified for broker.")
            if not self.celery_broker_queue:
                raise RuntimeError("Celery broker queue is not specified for broker.")
        else:
            raise RuntimeError(f"Unsupported Celery broker: {self.celery_broker}")
