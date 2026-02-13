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

import shlex
import sys
import click

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import Completer
    from prompt_toolkit.completion import Completion
    from prompt_toolkit.key_binding import KeyBindings
except ImportError:
    PromptSession = None

_COMMANDS: dict[str, click.BaseCommand] = {}

_BUILTIN_COMMANDS = {
    "help": "Show available commands or detailed help for a command",
    "exit": "Exit the REPL",
}


def register_commands(cli_group: click.Group) -> None:
    """Build the command dispatch table from the Click group."""
    _COMMANDS.clear()
    for name, cmd in cli_group.commands.items():
        _COMMANDS[name] = cmd


if PromptSession is not None:

    class SlashCommandCompleter(Completer):
        """Tab-completion and live suggestions for REPL slash commands and their options."""

        def get_completions(self, document, complete_event):
            text = document.text_before_cursor
            if not text.startswith("/"):
                return
            content = text[1:]
            if " " not in content:
                yield from self._complete_command(content)
            else:
                yield from self._complete_options(content, document)

        def _complete_command(self, prefix):
            """Yield command-name completions matching the typed prefix."""
            all_names = sorted(set(_COMMANDS) | set(_BUILTIN_COMMANDS))
            for name in all_names:
                if name.startswith(prefix):
                    if name in _BUILTIN_COMMANDS:
                        meta = _BUILTIN_COMMANDS[name]
                    else:
                        meta = _COMMANDS[name].get_short_help_str(limit=50)
                    yield Completion(name, start_position=-len(prefix), display_meta=meta)

        def _complete_options(self, content, document):
            """Yield option completions for the current command."""
            parts = content.split()
            cmd_name = parts[0]
            # /help <prefix> completes to command names
            if cmd_name == "help":
                yield from self._complete_help_args(parts, document)
                return
            if cmd_name not in _COMMANDS:
                return
            cmd = _COMMANDS[cmd_name]
            word = document.get_word_before_cursor(WORD=True)
            # Only suggest options when the cursor is after a space or the word starts with -
            if word and not word.startswith("-"):
                return
            # Exclude the word currently being typed from the "already used" set
            args_tokens = list(parts[1:])
            if word.startswith("-") and args_tokens and args_tokens[-1] == word:
                args_tokens = args_tokens[:-1]
            used = set(args_tokens)
            filter_prefix = word if word.startswith("-") else ""
            start_pos = -len(word) if word.startswith("-") else 0
            for param in cmd.params:
                if not isinstance(param, click.Option):
                    continue
                for opt in param.opts + param.secondary_opts:
                    if opt in used:
                        continue
                    if opt.startswith(filter_prefix):
                        yield Completion(opt, start_position=start_pos, display_meta=param.help or "")

        def _complete_help_args(self, parts, document):
            """Yield command-name completions for /help <cmd>."""
            word = document.get_word_before_cursor(WORD=True)
            # Only complete the first argument (the command name)
            if len(parts) > 2 or (len(parts) == 2 and not word):
                return
            prefix = word if word else ""
            start_pos = -len(prefix) if prefix else 0
            all_names = sorted(set(_COMMANDS) | set(_BUILTIN_COMMANDS))
            for name in all_names:
                if name.startswith(prefix):
                    if name in _BUILTIN_COMMANDS:
                        meta = _BUILTIN_COMMANDS[name]
                    else:
                        meta = _COMMANDS[name].get_short_help_str(limit=50)
                    yield Completion(name, start_position=start_pos, display_meta=meta)

    def _create_key_bindings():
        """Create custom key bindings for the REPL session."""
        bindings = KeyBindings()

        @bindings.add("escape", "escape")
        def _clear_line(event):
            """Double-Escape clears the current input line."""
            event.current_buffer.reset()

        return bindings


def _create_session():
    """Create a prompt_toolkit PromptSession with autocompletion, or None if unavailable."""
    if PromptSession is None:
        return None
    try:
        if not sys.stdin.isatty():
            return None
        return PromptSession(
            "cl> ",
            completer=SlashCommandCompleter(),
            complete_while_typing=True,
            auto_suggest=AutoSuggestFromHistory(),
            key_bindings=_create_key_bindings(),
        )
    except Exception:
        return None


def run_repl(ctx: click.Context) -> None:
    """Main REPL loop. Called when CLI is invoked without a subcommand."""

    # Mark context so commands can detect REPL mode
    ctx.ensure_object(dict)
    ctx.obj["repl"] = True

    click.echo("CompatibL Runtime CLI")
    click.echo("Type /help for available commands, /help <cmd> for details, /exit to quit.")
    click.echo()
    click.echo("Keyboard shortcuts:")
    click.echo("  Tab            Accept completion")
    click.echo("  Up/Down        Navigate history or completion menu")
    click.echo("  Escape Escape  Clear the current input line")
    click.echo("  Ctrl+C         Cancel current input")
    click.echo("  Ctrl+D         Exit REPL")
    click.echo()

    session = _create_session()

    while True:
        try:
            if session is not None:
                line = session.prompt()
            else:
                line = input("cl> ")
        except EOFError:
            click.echo()
            break
        except KeyboardInterrupt:
            click.echo()
            continue

        line = line.strip()
        if not line:
            continue

        if not line.startswith("/"):
            click.echo(f"Unknown input. Did you mean /{line}? Commands start with /.")
            continue

        try:
            parts = shlex.split(line[1:], posix=sys.platform != "win32")
        except ValueError as e:
            click.echo(f"Parse error: {e}")
            continue

        if not parts:
            continue

        cmd_name = parts[0]
        cmd_args = parts[1:]

        if cmd_name == "exit":
            break

        if cmd_name == "help":
            _show_help(cmd_args[0] if cmd_args else None)
            continue

        if cmd_name not in _COMMANDS:
            click.echo(f"Unknown command: /{cmd_name}")
            click.echo("Type /help for available commands.")
            continue

        try:
            _COMMANDS[cmd_name].main(cmd_args, standalone_mode=False, parent=ctx)
        except click.exceptions.Exit:
            pass
        except Exception as e:
            click.echo(f"Error: {e}", err=True)


def _show_help(cmd_name: str | None = None) -> None:
    """Display available REPL commands, or detailed help for a specific command."""
    if cmd_name is None:
        click.echo("Available commands:")
        for name, cmd in sorted(_COMMANDS.items()):
            help_text = cmd.get_short_help_str(limit=60)
            click.echo(f"  /{name:<20s} {help_text}")
        for name, description in sorted(_BUILTIN_COMMANDS.items()):
            click.echo(f"  /{name:<20s} {description}")
        return

    if cmd_name in _COMMANDS:
        cmd = _COMMANDS[cmd_name]
        ctx = click.Context(cmd, info_name=cmd_name)
        click.echo(cmd.get_help(ctx))
    elif cmd_name in _BUILTIN_COMMANDS:
        click.echo(f"/{cmd_name}: {_BUILTIN_COMMANDS[cmd_name]}")
    else:
        click.echo(f"Unknown command: /{cmd_name}")
        click.echo("Type /help for available commands.")
