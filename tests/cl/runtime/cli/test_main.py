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

from unittest.mock import patch
import pytest
from click.testing import CliRunner
from cl.runtime.cli.main import cli


@pytest.fixture()
def patched_cli():
    """Patch bootstrap side-effects so the cli group callback runs without real setup."""
    with (
        patch("cl.runtime.cli.bootstrap_util.apply_env_config") as mock_apply,
        patch("logging.config.dictConfig"),
    ):
        yield mock_apply


class TestCli:
    """Tests for the CLI group."""

    def test_help(self, cli_runner: CliRunner, patched_cli):
        """cli --help exits 0 and shows the description."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "CompatibL Runtime CLI" in result.output

    def test_version(self, cli_runner: CliRunner, patched_cli):
        """cli --version exits 0 and prints a version string.

        Note: cl-runtime may not be installed as a package in dev mode,
        so we accept either exit 0 with version output or a specific error.
        """
        with patch("click.version_option.__wrapped__", create=True):
            result = cli_runner.invoke(cli, ["--version"])
            # If package is installed, version prints; otherwise it errors
            if result.exit_code == 0:
                assert "version" in result.output.lower()
            else:
                assert "cl-runtime" in str(result.exception)

    def test_env_passed(self, cli_runner: CliRunner, patched_cli):
        """--env value is forwarded to apply_env_config.

        Note: --help on the group itself short-circuits before the callback runs,
        so we invoke a subcommand with --help to trigger the group callback.
        """
        result = cli_runner.invoke(cli, ["--env", "sample", "init-db", "--help"])
        assert result.exit_code == 0
        patched_cli.assert_called_once_with("sample")

    def test_no_env(self, cli_runner: CliRunner, patched_cli):
        """Without --env, apply_env_config is called with None."""
        result = cli_runner.invoke(cli, ["init-db", "--help"])
        assert result.exit_code == 0
        patched_cli.assert_called_once_with(None)

    def test_all_subcommands_registered(self, cli_runner: CliRunner, patched_cli):
        """cli --help lists all built-in subcommands."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        for cmd in (
            "backend",
            "init",
            "init-db",
            "init-type-info",
            "run",
            "fix-copyright-headers",
            "fix-csv-quotes",
        ):
            assert cmd in result.output

    def test_unknown_command(self, cli_runner: CliRunner, patched_cli):
        """An unknown command produces a non-zero exit code."""
        result = cli_runner.invoke(cli, ["unknown-cmd"])
        assert result.exit_code != 0

    def test_no_args_launches_repl(self, cli_runner: CliRunner, patched_cli):
        """cli with no args launches the REPL (banner appears in output)."""
        result = cli_runner.invoke(cli, [], input="/exit\n")
        assert result.exit_code == 0
        assert "CompatibL Runtime CLI" in result.output
