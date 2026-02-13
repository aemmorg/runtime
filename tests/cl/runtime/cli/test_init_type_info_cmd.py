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
from cl.runtime.cli.init_type_info_cmd import init_type_info


class TestInitTypeInfoCmd:
    """Tests for the init-type-info command."""

    def test_success(self, cli_runner: CliRunner):
        """init-type-info calls the tool function once."""
        with patch("tools.cl.runtime.init_type_info.init_type_info") as mock_tool:
            result = cli_runner.invoke(init_type_info, [])
            assert result.exit_code == 0
            mock_tool.assert_called_once()

    def test_error_propagates(self, cli_runner: CliRunner):
        """If the tool raises, the command exits with non-zero."""
        with patch("tools.cl.runtime.init_type_info.init_type_info", side_effect=RuntimeError("fail")):
            result = cli_runner.invoke(init_type_info, [])
            assert result.exit_code != 0

    def test_help(self, cli_runner: CliRunner):
        """init-type-info --help mentions type cache."""
        result = cli_runner.invoke(init_type_info, ["--help"])
        assert result.exit_code == 0
        assert "type cache" in result.output.lower() or "TypeInfo" in result.output
