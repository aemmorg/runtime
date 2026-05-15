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
import logging.config
import multiprocessing
import os
import signal
from dataclasses import dataclass
from logging.config import dictConfig
from typing import ClassVar
from typing import Dict
from typing import Final
from celery import Celery
from celery.exceptions import Reject
from celery.signals import setup_logging
from cl.runtime.contexts.context_manager import activate
from cl.runtime.contexts.context_manager import active
from cl.runtime.contexts.context_snapshot import ContextSnapshot
from cl.runtime.db.data_source import DataSource
from cl.runtime.log.log_config import celery_empty_logging_config
from cl.runtime.log.log_config import celery_worker_logging_config
from cl.runtime.server.env import Env
from cl.runtime.settings.celery_settings import CelerySettings
from cl.runtime.settings.env_settings import EnvSettings
from cl.runtime.tasks.celery.broker.celery_broker import CeleryBroker
from cl.runtime.tasks.task import Task
from cl.runtime.tasks.task_key import TaskKey
from cl.runtime.tasks.task_query import TaskQuery
from cl.runtime.tasks.task_queue import TaskQueue
from cl.runtime.tasks.task_status import TaskStatus

CELERY_RUN_COMMAND_QUEUE: Final[str] = "run_command"

celery_settings = CelerySettings.instance()

celery_app = Celery(
    "worker",
    broker=celery_settings.celery_broker_uri,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.task_track_started = True
celery_app.conf.task_default_queue = celery_settings.celery_broker_queue
celery_app.conf.task_time_limit = celery_settings.celery_time_limit
celery_app.conf.worker_prefetch_multiplier = 1  # One task per worker for better control


# Standalone function: @celery_app.task decorator is incompatible with class/static methods
@celery_app.task(max_retries=celery_settings.celery_max_retries, acks_late=True)  # Do not retry failed tasks
def celery_run_task(task_id: str, context_snapshot_json: str) -> None:
    """Invoke 'run_task' method of the specified task, delegates to CeleryQueue.run_task."""
    CeleryQueue.run_task(task_id, context_snapshot_json)


@dataclass(slots=True, kw_only=True)
class CeleryQueue(TaskQueue):
    """Execute tasks using Celery."""

    __celery_worker_process: ClassVar[multiprocessing.Process | None] = None
    __use_multiprocess_pool: ClassVar[bool] = False

    # max_workers: int = required()  # TODO: Implement support for max_workers
    """The maximum number of processes running concurrently."""

    @staticmethod
    @setup_logging.connect()
    def _config_loggers(*args, **kwargs):
        """Setup logging config for celery worker."""
        # Use empty config to suppress celery logger and propagate to root.
        dictConfig(celery_empty_logging_config)

    @classmethod
    def run_task(cls, task_id: str, context_snapshot_json: str) -> None:
        """Invoke 'run_task' method of the specified task."""

        # Deserialize context from 'context_data' parameter to run with the same settings as the caller context
        with ContextSnapshot.from_json(context_snapshot_json):
            # The task is running.
            running_query = TaskQuery(status=TaskStatus.RUNNING).build()
            running_tasks = active(DataSource).load_by_query(running_query, cast_to=Task)

            if len(running_tasks) >= celery_settings.celery_max_tenant_tasks:
                raise Reject("Tenant exceeded task limit", requeue=True)

            # Load and run the task
            task_key = TaskKey(task_id=task_id).build()
            task = active(DataSource).load_one(task_key, cast_to=Task)
            task.run_task()

    @classmethod
    def delete_existing_tasks(cls) -> None:
        """Delete the existing Celery tasks (will exit when the current process exits)."""
        broker = CeleryBroker.create(celery_settings.celery_broker_type)
        broker.delete_existing_tasks(celery_settings.celery_broker_uri, celery_settings.celery_broker_queue)

    @classmethod
    def _start_queue_callable(cls, *, log_config: Dict) -> None:
        """Callable for starting the celery queue process.

        Args:
            log_config: logging dict config from the main process.
        """

        # Setup logging config from the main process.
        logging.config.dictConfig(log_config)

        env_id = EnvSettings.instance().env_id
        celery_app.worker_main(
            argv=[
                "-A",
                "cl.runtime.tasks.celery.celery_queue",
                "worker",
                f"--hostname=celery-{env_id}-embedded@%h",
                "--loglevel=info",
                f"--pool={celery_settings.celery_pool_type}",
                f"--concurrency={celery_settings.celery_workers}",
            ],
        )

    @classmethod
    def run_start_queue(cls) -> None:
        """Start queue workers."""
        celery_settings = CelerySettings.instance()

        # Check if multiprocess pool is enabled
        if celery_settings.celery_multiprocess_pool:
            # Use new Manager for pool of processes
            from cl.runtime.tasks.celery.worker_process_manager import WorkerProcessManager

            cls.__use_multiprocess_pool = True
            manager = WorkerProcessManager.instance()
            manager.start_workers()
            logging.getLogger(__name__).info(
                f"Started multiprocess worker pool with {celery_settings.celery_workers} workers"
            )
        else:
            # Old mode - single embedded worker
            worker_process = multiprocessing.Process(
                target=cls._start_queue_callable,
                daemon=True,
                kwargs={"log_config": celery_worker_logging_config},
            )
            worker_process.start()
            cls.__celery_worker_process = worker_process

    @classmethod
    def run_stop_queue(cls) -> None:
        """Cancel all active runs and stop queue workers."""
        if cls.__use_multiprocess_pool:
            # Stop all processes through Manager
            from cl.runtime.tasks.celery.worker_process_manager import WorkerProcessManager

            manager = WorkerProcessManager.instance()
            manager.stop_workers()
            cls.__use_multiprocess_pool = False
        elif cls.__celery_worker_process is not None:
            # Old mode
            cls.__celery_worker_process.terminate()
            cls.__celery_worker_process.join()
            cls.__celery_worker_process = None

        if not CelerySettings.instance().celery_resume_on_launch:
            cls.delete_existing_tasks()

    def submit_task(self, task: TaskKey) -> None:

        # Wrap into Env
        with activate(Env().build()):

            # Get and serialize current context
            context_snapshot_json = ContextSnapshot.capture_active().to_json()

            # Pass parameters to the Celery task signature
            celery_run_task_signature = celery_run_task.s(
                task.task_id,
                context_snapshot_json,
            )

            # Submit task to Celery with completed and error links
            celery_run_task_signature.apply_async(
                task_id=task.task_id,  # Use our custom task ID instead of auto-generated UUID
                retry=False,  # Do not retry in case the task fails
                ignore_result=True,  # TODO: Do not publish to the Celery result backend
            )

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a specific task by ID. Returns True if cancellation was attempted."""
        try:
            logging.getLogger(__name__).info("Revoking task: %s", task_id)
            celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")
            return True
        except Exception as e:
            logging.getLogger(__name__).error("Failed to revoke task %s: %s", task_id, e)
            return False

    def cancel_tasks_batch(self, task_ids: list[str]) -> bool:
        """Cancel multiple tasks by killing workers and purging queue."""
        if not task_ids:
            return False

        try:
            celery_settings = CelerySettings.instance()
            logger = logging.getLogger(__name__)
            logger.info("Cancelling %d tasks", len(task_ids))

            # Single-worker mode: just revoke
            if not celery_settings.celery_multiprocess_pool or not self.__use_multiprocess_pool:
                celery_app.control.revoke(task_ids, terminate=True)
                return True

            # Multi-worker mode: kill all workers and purge queue
            from cl.runtime.tasks.celery.worker_process_manager import WorkerProcessManager

            manager = WorkerProcessManager.instance()
            worker_pids = manager.get_worker_pids()

            # Kill all workers
            for worker_id, pid in worker_pids.items():
                try:
                    os.kill(pid, signal.SIGTERM)
                    logger.info("Killed worker %d (PID %s)", worker_id, pid)
                except Exception as e:
                    logger.warning("Failed to kill worker %d: %s", worker_id, e)

            # Purge broker queue
            try:
                broker = CeleryBroker.create(celery_settings.celery_broker_type)
                broker.delete_existing_tasks(celery_settings.celery_broker_uri, celery_settings.celery_broker_queue)
                logger.info("Purged broker queue")
            except Exception as e:
                logger.warning("Failed to purge queue: %s", e)

            # Revoke in Celery
            celery_app.control.revoke(task_ids, terminate=True)
            return True

        except Exception as e:
            logger.error("Failed to cancel tasks: %s", e)
            return False
