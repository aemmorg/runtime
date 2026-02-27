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
from dataclasses import dataclass
from unittest.mock import patch
import click
from click.testing import CliRunner
from cl.runtime.cli.cli_command import CliCommand
from cl.runtime.cli.plugin_discovery import PluginGroup
from cl.runtime.cli.plugin_discovery import discover_cli_plugins

_TYPE_INFO_PATH = "cl.runtime.schema.type_info.TypeInfo"


@dataclass(slots=True, kw_only=True)
class _HelloCmd(CliCommand):
    """Test plugin command."""

    @classmethod
    def click_command(cls) -> click.BaseCommand:
        @click.command()
        def hello():
            """Say hello."""
            click.echo("hello from plugin")

        return hello


@dataclass(slots=True, kw_only=True)
class _GoodbyeCmd(CliCommand):
    """Another test plugin command."""

    @classmethod
    def click_command(cls) -> click.BaseCommand:
        @click.command()
        def goodbye():
            """Say goodbye."""
            click.echo("goodbye from plugin")

        return goodbye


def _make_group(**kwargs) -> click.Group:
    """Create a fresh Click group for testing."""
    return click.Group(name="test", **kwargs)


class TestDiscoverCliPlugins:
    """Tests for discover_cli_plugins()."""

    @patch(f"{_TYPE_INFO_PATH}.from_type_name", return_value=_HelloCmd)
    @patch(f"{_TYPE_INFO_PATH}.get_child_type_names", return_value=("_HelloCmd",))
    def test_discover_registers_command(self, mock_get_children, mock_from_name):
        """Plugin command is registered on the group."""
        group = _make_group()
        discover_cli_plugins(group)

        assert "hello" in group.commands
        runner = CliRunner()
        result = runner.invoke(group, ["hello"])
        assert result.exit_code == 0
        assert "hello from plugin" in result.output

    @patch(f"{_TYPE_INFO_PATH}.from_type_name", return_value=_HelloCmd)
    @patch(f"{_TYPE_INFO_PATH}.get_child_type_names", return_value=("_HelloCmd",))
    def test_discover_skips_existing(self, mock_get_children, mock_from_name):
        """Plugin with same name as built-in is skipped."""

        @click.command()
        def hello():
            """Built-in hello."""
            click.echo("built-in hello")

        group = _make_group(commands={"hello": hello})
        discover_cli_plugins(group)

        # Built-in command should be preserved
        runner = CliRunner()
        result = runner.invoke(group, ["hello"])
        assert result.exit_code == 0
        assert "built-in hello" in result.output

    @patch(f"{_TYPE_INFO_PATH}.from_type_name", side_effect=[ImportError("no module"), _GoodbyeCmd])
    @patch(f"{_TYPE_INFO_PATH}.get_child_type_names", return_value=("BadCmd", "_GoodbyeCmd"))
    def test_discover_import_error(self, mock_get_children, mock_from_name, caplog):
        """Import error for one plugin logs a warning but continues."""
        group = _make_group()
        with caplog.at_level(logging.WARNING):
            discover_cli_plugins(group)

        assert "goodbye" in group.commands
        assert "BadCmd" in caplog.text

    @patch(f"{_TYPE_INFO_PATH}.get_child_type_names", return_value=())
    def test_discover_empty(self, mock_get_children):
        """No child types results in no error and no new commands."""
        group = _make_group()
        discover_cli_plugins(group)

        assert len(group.commands) == 0

    @patch(f"{_TYPE_INFO_PATH}.from_type_name", return_value=_HelloCmd)
    @patch(f"{_TYPE_INFO_PATH}.get_child_type_names", return_value=("_HelloCmd",))
    def test_discover_idempotent(self, mock_get_children, mock_from_name):
        """Calling discover twice registers the command only once."""
        group = _make_group()
        discover_cli_plugins(group)
        discover_cli_plugins(group)

        assert list(group.commands.keys()).count("hello") == 1

    @patch(
        f"{_TYPE_INFO_PATH}.get_child_type_names",
        side_effect=FileNotFoundError("TypeInfo.csv not found"),
    )
    def test_discover_type_info_csv_missing(self, mock_get_children, caplog):
        """If TypeInfo CSV is missing, discovery logs a warning and returns gracefully."""
        group = _make_group()
        with caplog.at_level(logging.WARNING):
            discover_cli_plugins(group)

        assert len(group.commands) == 0
        assert "TypeInfo.csv" in caplog.text


class TestPluginGroup:
    """Tests for PluginGroup."""

    def setup_method(self):
        """Reset the class-level loaded flag before each test."""
        PluginGroup._plugins_loaded = False

    @patch(f"{_TYPE_INFO_PATH}.from_type_name", return_value=_HelloCmd)
    @patch(f"{_TYPE_INFO_PATH}.get_child_type_names", return_value=("_HelloCmd",))
    def test_list_commands_includes_plugins(self, mock_get_children, mock_from_name):
        """PluginGroup.list_commands() includes discovered plugin names."""
        group = PluginGroup(name="test")
        ctx = click.Context(group)
        commands = group.list_commands(ctx)

        assert "hello" in commands

    @patch(f"{_TYPE_INFO_PATH}.from_type_name", return_value=_HelloCmd)
    @patch(f"{_TYPE_INFO_PATH}.get_child_type_names", return_value=("_HelloCmd",))
    def test_get_command_returns_plugin(self, mock_get_children, mock_from_name):
        """PluginGroup.get_command() returns a discovered plugin command."""
        group = PluginGroup(name="test")
        ctx = click.Context(group)
        cmd = group.get_command(ctx, "hello")

        assert cmd is not None
        assert cmd.name == "hello"
