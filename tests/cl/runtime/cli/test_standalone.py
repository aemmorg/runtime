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
import sys
from unittest.mock import patch
import click
import pytest
from cl.runtime.cli._standalone import run_command


def _make_test_command():
    """Create a simple Click command for testing."""

    @click.command("test-cmd")
    @click.option("--flag", is_flag=True, default=False)
    @click.option("--value", default=None)
    def test_cmd(flag, value):
        """A test command."""
        click.echo(f"flag={flag} value={value}")

    return test_cmd


class TestRunCommand:
    """Tests for the run_command standalone bootstrap helper."""

    def test_parses_env(self):
        """--env win_sqlite is parsed and stripped from args."""
        test_cmd = _make_test_command()
        saved = os.environ.pop("CL_SETTINGS_ENV", None)
        try:
            with (
                patch("sys.argv", ["test_cmd", "--env", "win_sqlite", "--flag"]),
                patch("logging.config.dictConfig"),
            ):
                with pytest.raises(SystemExit) as exc_info:
                    run_command(test_cmd)
                assert exc_info.value.code == 0
                assert os.environ.get("CL_SETTINGS_ENV") == "win_sqlite"
        finally:
            if saved is not None:
                os.environ["CL_SETTINGS_ENV"] = saved
            else:
                os.environ.pop("CL_SETTINGS_ENV", None)

    def test_parses_env_equals(self):
        """--env=win_sqlite form is parsed and stripped."""
        test_cmd = _make_test_command()
        saved = os.environ.pop("CL_SETTINGS_ENV", None)
        try:
            with (
                patch("sys.argv", ["test_cmd", "--env=win_sqlite", "--flag"]),
                patch("logging.config.dictConfig"),
            ):
                with pytest.raises(SystemExit) as exc_info:
                    run_command(test_cmd)
                assert exc_info.value.code == 0
                assert os.environ.get("CL_SETTINGS_ENV") == "win_sqlite"
        finally:
            if saved is not None:
                os.environ["CL_SETTINGS_ENV"] = saved
            else:
                os.environ.pop("CL_SETTINGS_ENV", None)

    def test_no_env(self):
        """Without --env, command runs without setting CL_SETTINGS_ENV."""
        test_cmd = _make_test_command()
        saved = os.environ.pop("CL_SETTINGS_ENV", None)
        try:
            with (
                patch("sys.argv", ["test_cmd", "--flag"]),
                patch("logging.config.dictConfig"),
            ):
                with pytest.raises(SystemExit) as exc_info:
                    run_command(test_cmd)
                assert exc_info.value.code == 0
                assert "CL_SETTINGS_ENV" not in os.environ
        finally:
            if saved is not None:
                os.environ["CL_SETTINGS_ENV"] = saved

    def test_passes_args(self, capsys):
        """Remaining args after --env stripping are passed to the Click command."""
        test_cmd = _make_test_command()
        with (
            patch("sys.argv", ["test_cmd", "--env", "win_sqlite", "--flag", "--value", "hello"]),
            patch("logging.config.dictConfig"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                run_command(test_cmd)
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "flag=True" in captured.out
            assert "value=hello" in captured.out

    def test_prog_name(self, capsys):
        """--help output shows the Click command name as prog_name."""
        test_cmd = _make_test_command()
        with (
            patch("sys.argv", ["__main__", "--help"]),
            patch("logging.config.dictConfig"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                run_command(test_cmd)
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "Usage: test-cmd" in captured.out

    def test_bootstrap_idempotent(self):
        """Works when bootstrap is already loaded (test environment)."""
        assert "cl.runtime.bootstrap" in sys.modules
        test_cmd = _make_test_command()
        with (
            patch("sys.argv", ["test_cmd", "--flag"]),
            patch("logging.config.dictConfig"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                run_command(test_cmd)
            assert exc_info.value.code == 0
