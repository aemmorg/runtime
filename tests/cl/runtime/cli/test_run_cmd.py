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
from contextlib import contextmanager
from unittest.mock import MagicMock
from unittest.mock import patch
from click.testing import CliRunner
from cl.runtime.cli.run_cmd import _output_result
from cl.runtime.cli.run_cmd import run


@contextmanager
def _mock_activate_ds():
    """No-op context manager replacing activate_data_source."""
    yield MagicMock()


class TestRunCmdSync:
    """Tests for the run command in synchronous mode."""

    def test_sync_success(self, cli_runner: CliRunner):
        """run MyType MyMethod returns JSON result on stdout."""
        with (
            patch("cl.runtime.cli.bootstrap_util.activate_data_source", _mock_activate_ds),
            patch("cl.runtime.routers.task.run_request.RunRequest") as mock_req_cls,
            patch("cl.runtime.routers.task.run_response_util.RunResponseUtil.get_response") as mock_get_resp,
        ):
            mock_get_resp.return_value = {"status": "ok"}
            result = cli_runner.invoke(run, ["MyType", "MyMethod"])
            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output == {"status": "ok"}

    def test_sync_with_key(self, cli_runner: CliRunner):
        """--key is passed to RunRequest."""
        with (
            patch("cl.runtime.cli.bootstrap_util.activate_data_source", _mock_activate_ds),
            patch("cl.runtime.routers.task.run_request.RunRequest") as mock_req_cls,
            patch("cl.runtime.routers.task.run_response_util.RunResponseUtil.get_response") as mock_get_resp,
        ):
            mock_get_resp.return_value = {}
            result = cli_runner.invoke(run, ["MyType", "MyMethod", "--key", "some_key"])
            assert result.exit_code == 0
            mock_req_cls.assert_called_once_with(type="MyType", method="MyMethod", key="some_key", arguments=None)

    def test_sync_with_args(self, cli_runner: CliRunner):
        """--args JSON is parsed and passed to RunRequest."""
        with (
            patch("cl.runtime.cli.bootstrap_util.activate_data_source", _mock_activate_ds),
            patch("cl.runtime.routers.task.run_request.RunRequest") as mock_req_cls,
            patch("cl.runtime.routers.task.run_response_util.RunResponseUtil.get_response") as mock_get_resp,
        ):
            mock_get_resp.return_value = {}
            result = cli_runner.invoke(run, ["MyType", "MyMethod", "--args", '{"p": 1}'])
            assert result.exit_code == 0
            mock_req_cls.assert_called_once_with(type="MyType", method="MyMethod", key=None, arguments={"p": 1})

    def test_sync_output_file(self, cli_runner: CliRunner, tmp_path):
        """--output writes result to file instead of stdout."""
        output_file = str(tmp_path / "result.json")
        with (
            patch("cl.runtime.cli.bootstrap_util.activate_data_source", _mock_activate_ds),
            patch("cl.runtime.routers.task.run_request.RunRequest"),
            patch("cl.runtime.routers.task.run_response_util.RunResponseUtil.get_response") as mock_get_resp,
        ):
            mock_get_resp.return_value = {"result": 42}
            result = cli_runner.invoke(run, ["MyType", "MyMethod", "--output", output_file])
            assert result.exit_code == 0
            assert "Result written to" in result.output
            with open(output_file) as f:
                data = json.load(f)
            assert data == {"result": 42}

    def test_sync_invalid_json(self, cli_runner: CliRunner):
        """--args with invalid JSON produces a non-zero exit."""
        result = cli_runner.invoke(run, ["MyType", "MyMethod", "--args", "bad json"])
        assert result.exit_code != 0


class TestRunCmdAsync:
    """Tests for the run command in async mode."""

    def _make_status_item(self, task_run_id="task-1", status_code="Completed", user_message=None):
        """Create a mock StatusResponseItem."""
        item = MagicMock()
        item.task_run_id = task_run_id
        item.status_code = status_code
        item.user_message = user_message
        item.model_dump.return_value = {
            "task_run_id": task_run_id,
            "status_code": status_code,
            "user_message": user_message,
        }
        return item

    def _async_patches(self):
        """Return a dict of common patches for async tests."""
        return {
            "env": patch("cl.runtime.server.env.Env"),
            "ds": patch("cl.runtime.db.data_source.DataSource"),
            "eb": patch("cl.runtime.events.event_broker.EventBroker.create"),
            "activate": patch("cl.runtime.contexts.context_manager.activate"),
            "active": patch("cl.runtime.contexts.context_manager.active"),
            "task_util": patch("cl.runtime.tasks.task_util.TaskUtil.create_tasks"),
            "status": patch("cl.runtime.routers.task.status_response_item.StatusResponseItem.get_response"),
            "case": patch("cl.runtime.primitive.case_util.CaseUtil.pascal_to_snake_case"),
            "time": patch("cl.runtime.cli.run_cmd.time"),
            "task_queue": patch("cl.runtime.tasks.task_queue.TaskQueue"),
            "status_req": patch("cl.runtime.routers.task.status_request.StatusRequest"),
        }

    def test_async_success(self, cli_runner: CliRunner):
        """--async submits task and polls until Completed."""
        mock_task = MagicMock()
        mock_task.task_id = "task-1"

        completed_item = self._make_status_item(status_code="Completed")

        patches = self._async_patches()
        with (
            patches["env"],
            patches["ds"],
            patches["eb"],
            patches["activate"] as mock_activate,
            patches["active"] as mock_active,
            patches["task_util"] as mock_create_tasks,
            patches["status"] as mock_status_get,
            patches["case"] as mock_pascal,
            patches["time"] as mock_time,
            patches["task_queue"],
            patches["status_req"],
        ):

            @contextmanager
            def _fake_activate(obj):
                yield obj

            mock_activate.side_effect = _fake_activate
            mock_active.return_value = MagicMock()
            mock_create_tasks.return_value = [mock_task]
            mock_pascal.return_value = "my_method"
            mock_status_get.return_value = [completed_item]

            result = cli_runner.invoke(run, ["MyType", "MyMethod", "--async"])
            assert result.exit_code == 0
            assert "Submitted" in result.output
            assert "Completed" in result.output

    def test_async_failed_task(self, cli_runner: CliRunner):
        """--async with a failed task reports the error."""
        mock_task = MagicMock()
        mock_task.task_id = "task-1"

        failed_item = self._make_status_item(status_code="Failed", user_message="Something went wrong")

        patches = self._async_patches()
        with (
            patches["env"],
            patches["ds"],
            patches["eb"],
            patches["activate"] as mock_activate,
            patches["active"] as mock_active,
            patches["task_util"] as mock_create_tasks,
            patches["status"] as mock_status_get,
            patches["case"] as mock_pascal,
            patches["time"] as mock_time,
            patches["task_queue"],
            patches["status_req"],
        ):

            @contextmanager
            def _fake_activate(obj):
                yield obj

            mock_activate.side_effect = _fake_activate
            mock_active.return_value = MagicMock()
            mock_create_tasks.return_value = [mock_task]
            mock_pascal.return_value = "my_method"
            mock_status_get.return_value = [failed_item]

            result = cli_runner.invoke(run, ["MyType", "MyMethod", "--async"])
            # The command still completes (reports status)
            assert "Failed" in result.output
            assert "Something went wrong" in result.output

    def test_async_polling_loop(self, cli_runner: CliRunner):
        """Polling loop iterates when first poll returns Running, then Completed."""
        mock_task = MagicMock()
        mock_task.task_id = "task-1"

        running_item = self._make_status_item(status_code="Running")
        completed_item = self._make_status_item(status_code="Completed")

        patches = self._async_patches()
        with (
            patches["env"],
            patches["ds"],
            patches["eb"],
            patches["activate"] as mock_activate,
            patches["active"] as mock_active,
            patches["task_util"] as mock_create_tasks,
            patches["status"] as mock_status_get,
            patches["case"] as mock_pascal,
            patches["time"] as mock_time,
            patches["task_queue"],
            patches["status_req"],
        ):

            @contextmanager
            def _fake_activate(obj):
                yield obj

            mock_activate.side_effect = _fake_activate
            mock_active.return_value = MagicMock()
            mock_create_tasks.return_value = [mock_task]
            mock_pascal.return_value = "my_method"
            # First call returns Running, second returns Completed
            mock_status_get.side_effect = [[running_item], [completed_item]]

            result = cli_runner.invoke(run, ["MyType", "MyMethod", "--async"])
            assert result.exit_code == 0
            # time.sleep should have been called at least twice (one per loop)
            assert mock_time.sleep.call_count >= 2


class TestRunCmdArgs:
    """Tests for run command argument handling."""

    def test_missing_type_name(self, cli_runner: CliRunner):
        """run without arguments exits non-zero."""
        result = cli_runner.invoke(run, [])
        assert result.exit_code != 0

    def test_missing_method_name(self, cli_runner: CliRunner):
        """run with only type name exits non-zero."""
        result = cli_runner.invoke(run, ["MyType"])
        assert result.exit_code != 0

    def test_help(self, cli_runner: CliRunner):
        """run --help mentions TYPE_NAME, --async, --output."""
        result = cli_runner.invoke(run, ["--help"])
        assert result.exit_code == 0
        assert "TYPE_NAME" in result.output
        assert "--async" in result.output
        assert "--output" in result.output


class TestOutputResult:
    """Tests for the _output_result helper."""

    def test_to_stdout(self, capsys):
        """_output_result writes JSON to stdout when no file specified."""
        _output_result({"key": "value"}, None)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data == {"key": "value"}

    def test_to_file(self, tmp_path):
        """_output_result writes JSON to a file when path is specified."""
        output_file = str(tmp_path / "out.json")
        _output_result({"key": "value"}, output_file)
        with open(output_file) as f:
            data = json.load(f)
        assert data == {"key": "value"}
