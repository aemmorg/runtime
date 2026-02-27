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
from click.testing import CliRunner
from cl.runtime.cli.init_db_cmd import init_db


class TestInitDbCmd:
    """Tests for the init-db command."""

    def test_default_interactive(self, cli_runner: CliRunner):
        """init-db without --force calls init_db(interactive=True)."""
        with patch("tools.cl.runtime.init_db.init_db") as mock_tool:
            result = cli_runner.invoke(init_db, [])
            assert result.exit_code == 0
            mock_tool.assert_called_once_with(interactive=True)

    def test_force_flag(self, cli_runner: CliRunner):
        """init-db --force calls init_db(interactive=False)."""
        with patch("tools.cl.runtime.init_db.init_db") as mock_tool:
            result = cli_runner.invoke(init_db, ["--force"])
            assert result.exit_code == 0
            mock_tool.assert_called_once_with(interactive=False)

    def test_error_propagates(self, cli_runner: CliRunner):
        """If the tool raises, the command exits with non-zero."""
        with patch("tools.cl.runtime.init_db.init_db", side_effect=RuntimeError("db error")):
            result = cli_runner.invoke(init_db, [])
            assert result.exit_code != 0

    def test_help(self, cli_runner: CliRunner):
        """init-db --help mentions --force."""
        result = cli_runner.invoke(init_db, ["--help"])
        assert result.exit_code == 0
        assert "--force" in result.output
