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

"""Test that two processes with different CL_ENV_ID get isolated Celery settings, queues, and DB results."""

import multiprocessing
import os
import traceback


def _child_settings_only(env_id: str, result_queue: multiprocessing.Queue) -> None:
    """Child process that verifies CelerySettings resolve to env_id-specific values."""
    os.environ["CL_ENV_ID"] = env_id

    from cl.runtime.settings.settings import Settings

    Settings._Settings__settings_dict.clear()

    from cl.runtime.settings.celery_settings import CelerySettings

    settings = CelerySettings.instance()

    result_queue.put(
        {
            "env_id": env_id,
            "celery_broker_uri": settings.celery_broker_uri,
            "celery_broker_queue": settings.celery_broker_queue,
        }
    )


def _child_run_task(
    env_id: str,
    db_id: str,
    param_1: str,
    param_2: str,
    result_queue: multiprocessing.Queue,
) -> None:
    """Child process: set up isolated env, create and run a task via Celery, report results."""
    try:
        os.environ["CL_ENV_ID"] = env_id

        from cl.runtime.settings.settings import Settings

        Settings._Settings__settings_dict.clear()

        from cl.runtime.contexts.context_manager import activate
        from cl.runtime.contexts.context_manager import active
        from cl.runtime.contexts.context_snapshot import ContextSnapshot
        from cl.runtime.db.data_source import DataSource
        from cl.runtime.db.db import Db
        from cl.runtime.events.event_broker import EventBroker
        from cl.runtime.schema.type_info import TypeInfo
        from cl.runtime.server.env import Env
        from cl.runtime.settings.celery_settings import CelerySettings
        from cl.runtime.settings.env_kind import EnvKind
        from cl.runtime.settings.sse_settings import SseSettings
        from cl.runtime.tasks.celery.celery_queue import CeleryQueue
        from cl.runtime.tasks.celery.celery_queue import celery_app
        from cl.runtime.tasks.celery.celery_queue import celery_run_task
        from cl.runtime.tasks.class_method_task import ClassMethodTask
        from cl.runtime.tasks.task import Task
        from cl.runtime.tasks.task_key import TaskKey
        from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_handlers import StubHandlers

        celery_settings = CelerySettings.instance()

        celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)

        with activate(Env(env_id=env_id, env_kind=EnvKind.TEST, env_dir=f"test_isolation_{env_id}").build()):
            db = Db.create(db_id=db_id)
            with activate(DataSource(db=db).build()) as ds:
                ds.drop_db()
                try:
                    sse_settings = SseSettings.instance()
                    broker_type = TypeInfo.from_type_name(sse_settings.sse_broker_type)
                    broker = EventBroker.create(broker_type=broker_type, broker_id=f"test-isolation-{env_id}")
                    with activate(broker):
                        queue = CeleryQueue(queue_id=f"isolation-queue-{env_id}").build()
                        active(DataSource).replace_one(queue, commit=True)

                        with activate(queue):
                            task = ClassMethodTask.create(
                                queue=queue.get_key(),
                                record_type=StubHandlers,
                                method_callable=StubHandlers.run_static_method_with_params_2a,
                            )
                            task.method_args = {"param_1": param_1, "param_2": param_2}
                            task = task.build()
                            active(DataSource).replace_one(task, commit=True)

                            context_json = ContextSnapshot.capture_active().to_json()
                            celery_run_task(task.task_id, context_json)

                            loaded_task = active(DataSource).load_one(
                                TaskKey(task_id=task.task_id).build(), cast_to=Task
                            )
                            all_tasks = tuple(active(DataSource).load_all(key_type=TaskKey))

                            result_queue.put(
                                {
                                    "env_id": env_id,
                                    "celery_broker_uri": celery_settings.celery_broker_uri,
                                    "celery_broker_queue": celery_settings.celery_broker_queue,
                                    "task_id": task.task_id,
                                    "task_status": loaded_task.status.name,
                                    "task_label": loaded_task.label,
                                    "all_task_ids": [t.task_id for t in all_tasks],
                                    "error": None,
                                }
                            )
                finally:
                    ds.drop_db()
    except Exception as e:
        result_queue.put({"env_id": env_id, "error": f"{e}\n{traceback.format_exc()}"})


def test_celery_env_id_isolation():
    """Verify two processes with different CL_ENV_ID produce non-overlapping Celery settings."""
    result_queue = multiprocessing.Queue()

    p1 = multiprocessing.Process(target=_child_settings_only, args=("Instance1", result_queue))
    p2 = multiprocessing.Process(target=_child_settings_only, args=("Instance2", result_queue))

    p1.start()
    p2.start()
    p1.join(timeout=30)
    p2.join(timeout=30)

    assert p1.exitcode == 0, f"Process 1 failed with exit code {p1.exitcode}"
    assert p2.exitcode == 0, f"Process 2 failed with exit code {p2.exitcode}"

    results = {}
    while not result_queue.empty():
        r = result_queue.get_nowait()
        results[r["env_id"]] = r

    assert "Instance1" in results, "Process Instance1 did not report results"
    assert "Instance2" in results, "Process Instance2 did not report results"

    a = results["Instance1"]
    b = results["Instance2"]

    # Broker URIs must differ and each must contain its own env_id
    assert a["celery_broker_uri"] != b["celery_broker_uri"]
    assert "Instance1" in a["celery_broker_uri"] or "instance1" in a["celery_broker_uri"].lower()
    assert "Instance2" in b["celery_broker_uri"] or "instance2" in b["celery_broker_uri"].lower()

    # Queue names must differ and each must contain its own env_id
    assert a["celery_broker_queue"] != b["celery_broker_queue"]
    assert "Instance1" in a["celery_broker_queue"] or "instance1" in a["celery_broker_queue"].lower()
    assert "Instance2" in b["celery_broker_queue"] or "instance2" in b["celery_broker_queue"].lower()

    # Neither should contain the other's env_id
    assert "Instance2" not in a["celery_broker_uri"]
    assert "Instance1" not in b["celery_broker_uri"]
    assert "Instance2" not in a["celery_broker_queue"]
    assert "Instance1" not in b["celery_broker_queue"]


def test_celery_task_isolation():
    """Verify two processes with different CL_ENV_ID run tasks in isolated DBs and Celery queues."""
    result_queue = multiprocessing.Queue()

    p1 = multiprocessing.Process(
        target=_child_run_task,
        args=("Instance1", "test;celery;isolation;instance1", "alpha", "one", result_queue),
    )
    p2 = multiprocessing.Process(
        target=_child_run_task,
        args=("Instance2", "test;celery;isolation;instance2", "beta", "two", result_queue),
    )

    p1.start()
    p2.start()
    p1.join(timeout=60)
    p2.join(timeout=60)

    assert p1.exitcode == 0, f"Process Instance1 exited with code {p1.exitcode}"
    assert p2.exitcode == 0, f"Process Instance2 exited with code {p2.exitcode}"

    results = {}
    while not result_queue.empty():
        r = result_queue.get_nowait()
        results[r["env_id"]] = r

    assert "Instance1" in results, "Process Instance1 did not report results"
    assert "Instance2" in results, "Process Instance2 did not report results"

    a = results["Instance1"]
    b = results["Instance2"]

    # Check no errors in child processes
    assert a["error"] is None, f"Instance1 error: {a['error']}"
    assert b["error"] is None, f"Instance2 error: {b['error']}"

    # Both tasks must have completed successfully
    assert a["task_status"] == "COMPLETED", f"Instance1 task status: {a['task_status']}"
    assert b["task_status"] == "COMPLETED", f"Instance2 task status: {b['task_status']}"

    # Celery broker URIs must be different (isolated broker databases)
    assert a["celery_broker_uri"] != b["celery_broker_uri"]
    assert "Instance1" in a["celery_broker_uri"] or "instance1" in a["celery_broker_uri"].lower()
    assert "Instance2" in b["celery_broker_uri"] or "instance2" in b["celery_broker_uri"].lower()

    # Celery queue names must be different (isolated task routing)
    assert a["celery_broker_queue"] != b["celery_broker_queue"]
    assert "Instance1" in a["celery_broker_queue"] or "instance1" in a["celery_broker_queue"].lower()
    assert "Instance2" in b["celery_broker_queue"] or "instance2" in b["celery_broker_queue"].lower()

    # Each DB must contain only its own task (no cross-contamination)
    assert len(a["all_task_ids"]) == 1, f"Instance1 DB has {len(a['all_task_ids'])} tasks, expected 1"
    assert len(b["all_task_ids"]) == 1, f"Instance2 DB has {len(b['all_task_ids'])} tasks, expected 1"
    assert a["task_id"] in a["all_task_ids"]
    assert b["task_id"] in b["all_task_ids"]

    # Task IDs must not appear in the other instance's DB
    assert a["task_id"] not in b["all_task_ids"], "Instance1 task found in Instance2 DB"
    assert b["task_id"] not in a["all_task_ids"], "Instance2 task found in Instance1 DB"
