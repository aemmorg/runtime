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
from unittest.mock import patch
import pytest
from click.testing import CliRunner
from ruamel.yaml import YAML
from cl.runtime.cli.init_cmd import _write_settings_yaml
from cl.runtime.cli.init_cmd import init


class TestInitCmd:
    """Tests for the init command."""

    def test_non_interactive_success(self, cli_runner: CliRunner):
        """init --non-interactive calls scaffold tools and reports completion."""
        with (
            patch("tools.cl.runtime.init_project.init_project") as mock_scaffold,
            patch("tools.cl.runtime.init_type_info.init_type_info") as mock_type_info,
        ):
            result = cli_runner.invoke(init, ["--non-interactive"])
            assert result.exit_code == 0
            assert "complete" in result.output.lower()
            mock_scaffold.assert_called_once()
            mock_type_info.assert_called_once()

    def test_wizard_full_flow(self, cli_runner: CliRunner, tmp_path):
        """Simulated input through all 4 wizard pages succeeds."""
        # Input: Yes to continue, project-name, package, mongo, project-dir, Yes to proceed
        wizard_input = f"y\ntest-proj\ncl.test\nmongo\n{tmp_path}\ny\n"
        with (
            patch("tools.cl.runtime.init_project.init_project"),
            patch("tools.cl.runtime.init_type_info.init_type_info"),
        ):
            result = cli_runner.invoke(init, [], input=wizard_input)
            assert result.exit_code == 0
            assert "complete" in result.output.lower()

    def test_wizard_abort_first_confirm(self, cli_runner: CliRunner):
        """Answering 'n' at page 1 aborts the wizard."""
        result = cli_runner.invoke(init, [], input="n\n")
        assert result.exit_code == 0
        assert "Aborted" in result.output

    def test_wizard_abort_review(self, cli_runner: CliRunner, tmp_path):
        """Answering 'n' at the review page aborts the wizard."""
        # Input: Yes to continue, defaults for prompts, then No at review
        wizard_input = f"y\nmy-project\ncl.myapp\nmongo\n{tmp_path}\nn\n"
        result = cli_runner.invoke(init, [], input=wizard_input)
        assert result.exit_code == 0
        assert "Aborted" in result.output

    def test_wizard_defaults(self, cli_runner: CliRunner, tmp_path):
        """Pressing Enter for all prompts uses the defaults."""
        # Input: Yes to continue, Enter (default) x4, Yes to proceed
        wizard_input = f"y\n\n\n\n{tmp_path}\ny\n"
        with (
            patch("tools.cl.runtime.init_project.init_project"),
            patch("tools.cl.runtime.init_type_info.init_type_info"),
        ):
            result = cli_runner.invoke(init, [], input=wizard_input)
            assert result.exit_code == 0
            # Defaults should appear in the review
            assert "my-project" in result.output
            assert "cl.myapp" in result.output

    def test_wizard_sqlite(self, cli_runner: CliRunner, tmp_path):
        """Selecting sqlite sets the correct db_type in settings."""
        wizard_input = f"y\ntest-proj\ncl.test\nsqlite\n{tmp_path}\ny\n"
        with (
            patch("tools.cl.runtime.init_project.init_project"),
            patch("tools.cl.runtime.init_type_info.init_type_info"),
        ):
            result = cli_runner.invoke(init, [], input=wizard_input)
            assert result.exit_code == 0
            # Verify settings.yaml was written with sqlite config
            settings_path = os.path.join(str(tmp_path), "settings.yaml")
            if os.path.isfile(settings_path):
                yaml = YAML()
                with open(settings_path) as f:
                    settings = yaml.load(f)
                assert settings["default"]["db_type"] == "SqliteDb"

    def test_non_interactive_error(self, cli_runner: CliRunner):
        """init --non-interactive propagates errors from scaffold tools."""
        with (
            patch("tools.cl.runtime.init_project.init_project", side_effect=RuntimeError("scaffold failed")),
            patch("tools.cl.runtime.init_type_info.init_type_info"),
        ):
            result = cli_runner.invoke(init, ["--non-interactive"])
            assert result.exit_code != 0


class TestWriteSettingsYaml:
    """Tests for the _write_settings_yaml helper."""

    def test_mongo_settings(self, tmp_path):
        """_write_settings_yaml writes correct YAML for mongo."""
        _write_settings_yaml(str(tmp_path), "my-proj", "cl.myapp", "mongo")
        settings_path = os.path.join(str(tmp_path), "settings.yaml")
        assert os.path.isfile(settings_path)

        yaml = YAML()
        with open(settings_path) as f:
            settings = yaml.load(f)

        default = settings["default"]
        assert default["db_type"] == "BasicMongoDb"
        assert "db_mongo_uri" in default
        assert default["api_port"] == 7008
        assert default["package_source_dirs"]["cl.runtime"] == "runtime"

    def test_sqlite_settings(self, tmp_path):
        """_write_settings_yaml writes correct YAML for sqlite."""
        _write_settings_yaml(str(tmp_path), "my-proj", "cl.myapp", "sqlite")
        settings_path = os.path.join(str(tmp_path), "settings.yaml")

        yaml = YAML()
        with open(settings_path) as f:
            settings = yaml.load(f)

        default = settings["default"]
        assert default["db_type"] == "SqliteDb"
        assert "db_mongo_uri" not in default
