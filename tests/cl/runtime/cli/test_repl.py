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
from prompt_toolkit.document import Document
from cl.runtime.cli.main import cli
from cl.runtime.cli.repl import _COMMANDS
from cl.runtime.cli.repl import register_commands
from cl.runtime.cli.repl import SlashCommandCompleter


@pytest.fixture()
def patched_cli():
    """Patch bootstrap side-effects so the cli group callback runs without real setup."""
    with (
        patch("cl.runtime.cli.bootstrap_util.apply_env_config"),
        patch("logging.config.dictConfig"),
    ):
        yield


@pytest.fixture()
def completer():
    """Return a SlashCommandCompleter with CLI commands registered."""
    register_commands(cli)
    yield SlashCommandCompleter()
    _COMMANDS.clear()


class TestRepl:
    """Tests for the interactive REPL mode."""

    def test_repl_launches_on_no_args(self, cli_runner: CliRunner, patched_cli):
        """cli with no subcommand enters the REPL and shows the banner with keyboard shortcuts."""
        result = cli_runner.invoke(cli, [], input="/exit\n")
        assert result.exit_code == 0
        assert "CompatibL Runtime CLI" in result.output
        assert "Keyboard shortcuts:" in result.output
        assert "Escape Escape" in result.output
        assert "Ctrl+C" in result.output
        assert "Ctrl+D" in result.output

    def test_repl_exit(self, cli_runner: CliRunner, patched_cli):
        """Input /exit exits cleanly."""
        result = cli_runner.invoke(cli, [], input="/exit\n")
        assert result.exit_code == 0

    def test_repl_eof(self, cli_runner: CliRunner, patched_cli):
        """Empty input (EOF) exits cleanly."""
        result = cli_runner.invoke(cli, [], input="")
        assert result.exit_code == 0
        assert "CompatibL Runtime CLI" in result.output

    def test_repl_help(self, cli_runner: CliRunner, patched_cli):
        """Input /help lists all registered commands."""
        result = cli_runner.invoke(cli, [], input="/help\n/exit\n")
        assert result.exit_code == 0
        assert "Available commands:" in result.output
        assert "/init-db" in result.output
        assert "/run" in result.output
        assert "/help" in result.output
        assert "/exit" in result.output

    def test_repl_help_command(self, cli_runner: CliRunner, patched_cli):
        """/help init-db shows the detailed help for that command."""
        result = cli_runner.invoke(cli, [], input="/help init-db\n/exit\n")
        assert result.exit_code == 0
        assert "--force" in result.output
        assert "Initialize the database" in result.output

    def test_repl_help_builtin(self, cli_runner: CliRunner, patched_cli):
        """/help exit shows the builtin description."""
        result = cli_runner.invoke(cli, [], input="/help exit\n/exit\n")
        assert result.exit_code == 0
        assert "/exit:" in result.output
        assert "Exit the REPL" in result.output

    def test_repl_help_unknown(self, cli_runner: CliRunner, patched_cli):
        """/help bogus shows an unknown command message."""
        result = cli_runner.invoke(cli, [], input="/help bogus\n/exit\n")
        assert result.exit_code == 0
        assert "Unknown command: /bogus" in result.output

    def test_repl_dispatch_command(self, cli_runner: CliRunner, patched_cli):
        """/init-db --force dispatches to the init-db command."""
        with patch("tools.cl.runtime.init_db.init_db") as mock_tool:
            result = cli_runner.invoke(cli, [], input="/init-db --force\n/exit\n")
            assert result.exit_code == 0
            mock_tool.assert_called_once_with(interactive=False)

    def test_repl_invalid_command(self, cli_runner: CliRunner, patched_cli):
        """/bogus shows an unknown command message."""
        result = cli_runner.invoke(cli, [], input="/bogus\n/exit\n")
        assert result.exit_code == 0
        assert "Unknown command: /bogus" in result.output

    def test_repl_empty_line(self, cli_runner: CliRunner, patched_cli):
        """Blank lines are ignored."""
        result = cli_runner.invoke(cli, [], input="\n\n/exit\n")
        assert result.exit_code == 0

    def test_repl_no_slash_prefix(self, cli_runner: CliRunner, patched_cli):
        """Input without slash prefix gives a hint."""
        result = cli_runner.invoke(cli, [], input="init-db\n/exit\n")
        assert result.exit_code == 0
        assert "Did you mean /init-db?" in result.output

    def test_repl_command_error(self, cli_runner: CliRunner, patched_cli):
        """A command that raises an error shows the error but REPL continues."""
        with patch("tools.cl.runtime.init_db.init_db", side_effect=RuntimeError("db error")):
            result = cli_runner.invoke(cli, [], input="/init-db\n/exit\n")
            assert result.exit_code == 0
            assert "db error" in result.output

    def test_repl_subcommand_still_works(self, cli_runner: CliRunner, patched_cli):
        """Providing a subcommand directly still works (no REPL)."""
        with patch("tools.cl.runtime.init_db.init_db") as mock_tool:
            result = cli_runner.invoke(cli, ["init-db", "--force"])
            assert result.exit_code == 0
            mock_tool.assert_called_once_with(interactive=False)
            assert "CompatibL Runtime CLI" not in result.output


class TestSlashCommandCompleter:
    """Tests for the slash command autocompletion."""

    @staticmethod
    def _complete(completer, text):
        """Get completions for the given input text."""
        doc = Document(text, len(text))
        return list(completer.get_completions(doc, None))

    def test_slash_shows_all_commands(self, completer):
        """Typing / shows all commands including builtins."""
        completions = self._complete(completer, "/")
        names = {c.text for c in completions}
        assert "init-db" in names
        assert "run" in names
        assert "help" in names
        assert "exit" in names

    def test_prefix_filters_commands(self, completer):
        """Typing /ini filters to matching commands."""
        completions = self._complete(completer, "/ini")
        names = {c.text for c in completions}
        assert "init" in names
        assert "init-db" in names
        assert "init-type-info" in names
        assert "run" not in names
        assert "exit" not in names

    def test_completions_have_descriptions(self, completer):
        """Each completion includes a non-empty description."""
        completions = self._complete(completer, "/")
        for c in completions:
            assert c.display_meta is not None
            assert str(c.display_meta) != ""

    def test_no_completions_without_slash(self, completer):
        """Text not starting with / yields no completions."""
        completions = self._complete(completer, "init")
        assert completions == []

    def test_empty_text_no_completions(self, completer):
        """Empty text yields no completions."""
        completions = self._complete(completer, "")
        assert completions == []

    def test_option_completion_after_space(self, completer):
        """After /init-db (space), options are suggested."""
        completions = self._complete(completer, "/init-db ")
        names = {c.text for c in completions}
        assert "--force" in names

    def test_option_prefix_filter(self, completer):
        """Typing --f filters to matching options only."""
        completions = self._complete(completer, "/init-db --f")
        names = {c.text for c in completions}
        assert "--force" in names
        assert "--help" not in names

    def test_used_options_excluded(self, completer):
        """Already-used options are not suggested again."""
        completions = self._complete(completer, "/init-db --force ")
        names = {c.text for c in completions}
        assert "--force" not in names

    def test_no_options_for_unknown_command(self, completer):
        """Unknown command yields no option completions."""
        completions = self._complete(completer, "/bogus --")
        assert completions == []

    def test_no_options_when_typing_argument(self, completer):
        """When typing a non-option argument value, no options are suggested."""
        completions = self._complete(completer, "/run MyType")
        assert completions == []

    def test_run_options_after_arguments(self, completer):
        """Options are suggested after positional arguments for the run command."""
        completions = self._complete(completer, "/run MyType MyMethod --")
        names = {c.text for c in completions}
        assert "--key" in names
        assert "--args" in names
        assert "--output" in names

    def test_start_position_command(self, completer):
        """Command completion start_position replaces the typed prefix."""
        completions = self._complete(completer, "/ini")
        for c in completions:
            assert c.start_position == -3

    def test_start_position_option(self, completer):
        """Option completion start_position replaces the typed option prefix."""
        completions = self._complete(completer, "/init-db --f")
        for c in completions:
            assert c.start_position == -3

    def test_start_position_after_space(self, completer):
        """Options inserted at cursor when preceded by a space."""
        completions = self._complete(completer, "/init-db ")
        for c in completions:
            assert c.start_position == 0

    def test_builtin_descriptions(self, completer):
        """Built-in commands have the expected descriptions."""
        completions = self._complete(completer, "/hel")
        match = [c for c in completions if c.text == "help"]
        assert len(match) == 1
        assert "help" in str(match[0].display_meta).lower()

    def test_help_completes_command_names(self, completer):
        """/help (space) suggests all command names."""
        completions = self._complete(completer, "/help ")
        names = {c.text for c in completions}
        assert "init-db" in names
        assert "run" in names
        assert "help" in names
        assert "exit" in names

    def test_help_prefix_filters(self, completer):
        """/help ini filters to matching command names."""
        completions = self._complete(completer, "/help ini")
        names = {c.text for c in completions}
        assert "init-db" in names
        assert "run" not in names

    def test_help_no_second_arg(self, completer):
        """/help init-db (space) yields no further completions."""
        completions = self._complete(completer, "/help init-db ")
        assert completions == []
