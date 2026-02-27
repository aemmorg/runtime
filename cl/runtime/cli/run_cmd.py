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

import json
import time
from dataclasses import dataclass
import click
from cl.runtime.cli.cli_command import CliCommand


@dataclass(slots=True, kw_only=True)
class RunCmd(CliCommand):
    """CLI command to execute a handler method (sync or async)."""

    @classmethod
    def click_command(cls) -> click.BaseCommand:
        """Return the Click command to register on the CLI group."""

        @click.command()
        @click.argument("type_name")
        @click.argument("method_name")
        @click.option("--key", default=None, help="Record key for instance methods.")
        @click.option("--args", "args_json", default=None, help="Method arguments as a JSON string.")
        @click.option(
            "--async", "is_async", is_flag=True, default=False, help="Submit as an async task and poll for result."
        )
        @click.option("--output", "-o", "output_file", default=None, type=click.Path(), help="Write result to file.")
        def run(
            type_name: str,
            method_name: str,
            key: str | None,
            args_json: str | None,
            is_async: bool,
            output_file: str | None,
        ) -> None:
            """Execute a handler method (sync or async).

            TYPE_NAME is the short type name (e.g. DataSourceTool).
            METHOD_NAME is the method name in PascalCase (e.g. RunExport).
            """
            args_dict = json.loads(args_json) if args_json else None

            if is_async:
                _run_async(type_name, method_name, key, args_dict, output_file)
            else:
                _run_sync(type_name, method_name, key, args_dict, output_file)

        return run


run = RunCmd.click_command()


def _run_sync(
    type_name: str, method_name: str, key: str | None, args_dict: dict | None, output_file: str | None
) -> None:
    """Run a handler synchronously in the current process."""
    from cl.runtime.cli.bootstrap_util import activate_data_source
    from cl.runtime.routers.task.run_request import RunRequest
    from cl.runtime.routers.task.run_response_util import RunResponseUtil

    with activate_data_source():
        request = RunRequest(type=type_name, method=method_name, key=key, arguments=args_dict)
        result = RunResponseUtil.get_response(request)
        _output_result(result, output_file)


def _run_async(
    type_name: str, method_name: str, key: str | None, args_dict: dict | None, output_file: str | None
) -> None:
    """Submit a handler as an async task and poll until completion."""
    from cl.runtime.contexts.context_manager import activate
    from cl.runtime.contexts.context_manager import active
    from cl.runtime.db.data_source import DataSource
    from cl.runtime.events.event_broker import EventBroker
    from cl.runtime.primitive.case_util import CaseUtil
    from cl.runtime.routers.task.status_request import StatusRequest
    from cl.runtime.routers.task.status_response_item import StatusResponseItem
    from cl.runtime.server.env import Env
    from cl.runtime.tasks.task_queue import TaskQueue
    from cl.runtime.tasks.task_util import TaskUtil

    with activate(Env().build()), activate(DataSource().build()), activate(EventBroker.create()):
        ds = active(DataSource)
        task_queue = active(TaskQueue)

        tasks = TaskUtil.create_tasks(
            type_name=type_name,
            method_name=CaseUtil.pascal_to_snake_case(method_name),
            args=args_dict,
            str_keys=[key] if key else None,
        )

        task_run_ids = []
        for handler_task in tasks:
            ds.replace_one(handler_task, commit=True)
            task_queue.submit_task(handler_task)
            task_run_ids.append(handler_task.task_id)

        click.echo(f"Submitted {len(task_run_ids)} task(s): {', '.join(task_run_ids)}")

        # Poll for completion
        terminal_statuses = {"Completed", "Failed", "Cancelled"}
        poll_interval = 1.0
        while True:
            time.sleep(poll_interval)
            status_request = StatusRequest(task_run_ids=task_run_ids)
            status_items = StatusResponseItem.get_response(status_request)

            all_done = all(item.status_code in terminal_statuses for item in status_items)
            for item in status_items:
                click.echo(f"  Task {item.task_run_id}: {item.status_code}")

            if all_done:
                break

            # Back off gradually up to 5 seconds
            poll_interval = min(poll_interval * 1.5, 5.0)

        # Report final status
        for item in status_items:
            if item.status_code == "Failed" and item.user_message:
                click.echo(f"Error in task {item.task_run_id}: {item.user_message}", err=True)

        result = {"tasks": [item.model_dump() for item in status_items]}
        _output_result(result, output_file)


def _output_result(result: object, output_file: str | None) -> None:
    """Write result as JSON to stdout or to a file."""
    output = json.dumps(result, indent=2, default=str)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        click.echo(f"Result written to {output_file}")
    else:
        click.echo(output)


if __name__ == "__main__":
    from cl.runtime.cli._standalone import run_command

    run_command(run)
