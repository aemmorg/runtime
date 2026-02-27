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

from unittest.mock import MagicMock
from unittest.mock import patch
from click.testing import CliRunner
from cl.runtime.cli.fix_csv_quotes_cmd import fix_csv_quotes


class TestFixCsvQuotesCmd:
    """Tests for the fix-csv-quotes command."""

    def test_success(self, cli_runner: CliRunner):
        """fix-csv-quotes calls CsvReader.check_or_fix_quotes with correct args."""
        mock_pkg_settings = MagicMock()
        mock_pkg_settings.get_packages.return_value = ["cl.runtime"]

        with (
            patch("cl.runtime.settings.package_settings.PackageSettings.instance", return_value=mock_pkg_settings),
            patch("cl.runtime.project.project_util.ProjectUtil.get_package_source_root", return_value="/src"),
            patch("cl.runtime.project.project_util.ProjectUtil.get_package_stubs_root", return_value=None),
            patch("cl.runtime.project.project_util.ProjectUtil.get_package_tests_root", return_value=None),
            patch("cl.runtime.project.project_util.ProjectUtil.get_package_preloads_root", return_value=None),
            patch("cl.runtime.file.csv_reader.CsvReader.check_or_fix_quotes") as mock_fix,
        ):
            result = cli_runner.invoke(fix_csv_quotes, [])
            assert result.exit_code == 0
            mock_fix.assert_called_once()
            call_kwargs = mock_fix.call_args
            assert call_kwargs[1]["ext"] == "csv"
            assert call_kwargs[1]["apply_fix"] is True
            assert call_kwargs[1]["verbose"] is True

    def test_error_propagates(self, cli_runner: CliRunner):
        """If the tool raises, the command exits with non-zero."""
        mock_pkg_settings = MagicMock()
        mock_pkg_settings.get_packages.return_value = []

        with (
            patch("cl.runtime.settings.package_settings.PackageSettings.instance", return_value=mock_pkg_settings),
            patch(
                "cl.runtime.file.csv_reader.CsvReader.check_or_fix_quotes",
                side_effect=RuntimeError("csv error"),
            ),
        ):
            result = cli_runner.invoke(fix_csv_quotes, [])
            assert result.exit_code != 0

    def test_help(self, cli_runner: CliRunner):
        """fix-csv-quotes --help mentions CSV."""
        result = cli_runner.invoke(fix_csv_quotes, ["--help"])
        assert result.exit_code == 0
        assert "CSV" in result.output or "csv" in result.output.lower()
