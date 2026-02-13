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
import click
from cl.runtime.cli.cli_command import CliCommand
from cl.runtime.schema.type_info import TypeInfo

_logger = logging.getLogger(__name__)


def discover_cli_plugins(cli_group: click.Group) -> None:
    """Discover CliCommand subclasses via TypeInfo and register them on the CLI group.

    Each CliCommand subclass found in TypeInfo.csv is imported, its click_command()
    classmethod is called, and the resulting command is added to the group. Built-in
    commands take priority -- if a plugin command has the same name as an existing
    command, it is skipped.

    Errors during import or command creation are logged as warnings and do not
    break the CLI.
    """
    try:
        child_type_names = TypeInfo.get_child_type_names(CliCommand)
    except Exception as e:
        _logger.warning(f"Could not load CLI plugin type names: {e}")
        return

    for type_name in child_type_names:
        try:
            cmd_type = TypeInfo.from_type_name(type_name)
            cmd = cmd_type.click_command()
            if cmd.name in cli_group.commands:
                _logger.debug(f"CLI plugin '{cmd.name}' skipped (built-in command exists)")
                continue
            cli_group.add_command(cmd)
        except Exception as e:
            _logger.warning(f"Failed to load CLI plugin '{type_name}': {e}")


class PluginGroup(click.Group):
    """A Click group that lazily discovers plugin commands from TypeInfo.

    TypeInfo._ensure_loaded() only reads a static CSV file, so this works
    without full Dynaconf/bootstrap initialization -- making 'cl-runtime --help'
    show plugin commands.
    """

    _plugins_loaded: bool = False

    def _ensure_plugins(self) -> None:
        """Load plugin commands if not already loaded."""
        if PluginGroup._plugins_loaded:
            return
        PluginGroup._plugins_loaded = True
        try:
            discover_cli_plugins(self)
        except Exception as e:
            _logger.warning(f"Plugin discovery failed: {e}")

    def list_commands(self, ctx: click.Context) -> list[str]:
        self._ensure_plugins()
        return super().list_commands(ctx)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.BaseCommand | None:
        self._ensure_plugins()
        return super().get_command(ctx, cmd_name)
