# CLI Reference (`cl.runtime.cli`)

## Overview

The `cl.runtime.cli` package provides a Click-based command-line interface for CompatibL Runtime. It provides built-in subcommands for project initialization, database management, handler execution, and backend server lifecycle, plus an extensibility mechanism that lets downstream applications register custom commands via TypeInfo discovery.

The CLI can be invoked in three ways:

```bash
# 1. Via console script (works after pip install) or python -m (full CLI with all commands)
cl-runtime <command> [options]
python -m cl.runtime.cli <command> [options]

# 2. Via direct module invocation (single command, useful for scripting/debugging/IDE)
python -m cl.runtime.cli.<command_module> [options]

# 3. Via interactive REPL (enter without a subcommand)
cl-runtime
```

## Global Options

These options are available on every command and must appear **before** the subcommand name.

| Option | Description |
|--------|-------------|
| `--env NAME` | Dynaconf environment name to activate (e.g. `win_mongo`, `win_sqlite`, `docker`). Maps to the `CL_SETTINGS_ENV` environment variable. When omitted, Dynaconf uses its default environment (`development`). |
| `--version` | Print the installed `cl-runtime` package version and exit. |
| `--help` | Show the top-level help message with all available commands. |

Example:

```bash
python -m cl.runtime.cli --env win_sqlite init-db --force
cl-runtime --env win_mongo run DataSourceTool RunExport
cl-runtime --version
```

## Invocation Modes

### Full CLI (all commands)

```bash
cl-runtime <command> [options]
python -m cl.runtime.cli <command> [options]
```

### Direct module invocation (single command)

Run any individual command as a Python module without going through the CLI group. Useful for scripting, debugging, and IDE run configurations.

```bash
python -m cl.runtime.cli.init_db_cmd --force
python -m cl.runtime.cli.run_cmd MyType MyMethod --key k1
python -m cl.runtime.cli.init_db_cmd --env win_sqlite --force
```

The `--env NAME` option is supported on all standalone commands and is stripped before passing remaining args to the Click command.

**Available modules:**

| Command | Module |
|---------|--------|
| `backend` | `cl.runtime.cli.backend_cmd` |
| `init` | `cl.runtime.cli.init_cmd` |
| `init-db` | `cl.runtime.cli.init_db_cmd` |
| `init-type-info` | `cl.runtime.cli.init_type_info_cmd` |
| `run` | `cl.runtime.cli.run_cmd` |
| `fix-copyright-headers` | `cl.runtime.cli.fix_copyright_headers_cmd` |
| `fix-csv-quotes` | `cl.runtime.cli.fix_csv_quotes_cmd` |

### Interactive REPL

```bash
cl-runtime                    # enters REPL
cl-runtime --env win_sqlite   # enters REPL with env override
```

---

## Interactive Mode (REPL)

When invoked without a subcommand, the CLI enters an interactive REPL loop:

```bash
cl-runtime                    # enters REPL
cl-runtime --env win_sqlite   # enters REPL with env override
cl-runtime init-db --force    # runs command and exits (unchanged)
```

Inside the REPL, all commands are prefixed with `/`:

```
CompatibL Runtime CLI
Type /help for available commands, /help <cmd> for details, /exit to quit.

Keyboard shortcuts:
  Tab            Accept completion
  Up/Down        Navigate history or completion menu
  Escape Escape  Clear the current input line
  Ctrl+C         Cancel current input
  Ctrl+D         Exit REPL

cl> /init-db --force
cl> /run MyType MyMethod --key k1
{...json result...}
cl> /backend
Backend started (PID 12345) on http://localhost:7008 — log: C:\...\cl_runtime_backend.log
cl> /backend status
Backend running (PID 12345)  log: C:\...\cl_runtime_backend.log
cl> /backend log 5
--- backend log (5 of 42 lines) ---
...
--- end of log (C:\...\cl_runtime_backend.log) ---
cl> /backend stop
Backend (PID 12345) stopped.
cl> /help
Available commands:
  /backend              Manage the backend server
  /init-db              Initialize the database
  /run                  Execute a handler method
  ...
  /help                 Show available commands or /help <cmd> for details
  /exit                 Exit the REPL
cl> /exit
```

**Built-in REPL commands** (not dispatched through Click):

| Command | Description |
|---------|-------------|
| `/help` | List all available commands with short descriptions |
| `/help <cmd>` | Show detailed help for a specific command |
| `/exit` | Exit the REPL (also terminates any background backend process) |

All other commands (including `/backend` and its subcommands) are standard Click commands registered in `main.py`.

**Autocompletion:**

The REPL provides live autocompletion powered by `prompt_toolkit`:

- Type `/` to see a dropdown of all available commands with descriptions
- Continue typing to filter matches (e.g. `/ini` narrows to `init`, `init-db`, `init-type-info`)
- Press Tab or Enter to accept a completion
- After a command name, options (`--force`, `--key`, etc.) are suggested automatically
- Already-used options are excluded from suggestions

Autocompletion activates automatically in interactive terminals. When stdin is piped, the REPL falls back to plain `input()` with no completion.

**Keyboard shortcuts:**

| Shortcut | Behavior |
|----------|----------|
| Tab | Accept the selected completion |
| Up/Down | Navigate completion menu or recall history |
| Escape Escape | Clear the current input line |
| Ctrl+C | Cancel current command, stay in REPL |
| Ctrl+D | Exit REPL gracefully |

---

## Commands

### `backend` -- Backend Server Lifecycle

A Click command group that manages the FastAPI/Uvicorn backend server. When invoked without a subcommand, defaults to `start`.

```
cl-runtime backend [start] [--port PORT] [--no-browser]
cl-runtime backend stop
cl-runtime backend status
cl-runtime backend log [LINES]
```

| Subcommand | Description |
|------------|-------------|
| `start` | Start the backend server (default when no subcommand given). |
| `stop` | Terminate the running backend process. |
| `status` | Show whether a backend process is running, its PID/port, and log path. |
| `log [LINES]` | Show the last LINES of backend output (default: 20). |

| Option (on `start`) | Description |
|----------------------|-------------|
| `--port PORT` | Override the API port from settings. |
| `--no-browser` | Do not open a browser tab on startup. |

**CLI mode** (`cl-runtime backend`):

Launches the server in the **foreground** (blocks until Ctrl+C). Stdout/stderr are inherited so the user sees Uvicorn output directly.

```bash
cl-runtime backend
cl-runtime backend start --port 8080 --no-browser
```

**REPL mode** (`/backend`):

Launches the server as a **background** subprocess with output redirected to a temporary log file (`cl_runtime_backend.log` in the system temp directory). A one-line summary is printed with the PID, URL, and log path.

```
cl> /backend
Backend started (PID 12345) on http://localhost:7008 — log: /tmp/cl_runtime_backend.log
cl> /backend log
--- backend log (20 of 42 lines) ---
...
--- end of log (/tmp/cl_runtime_backend.log) ---
cl> /backend stop
Backend (PID 12345) stopped.
```

When the REPL exits, any tracked backend subprocess is automatically terminated (atexit handler registered at start time).

**Implementation notes:**

- The subprocess is launched as `[sys.executable, "-m", "cl.runtime"]` with the current environment. `--port` is forwarded as `CL_API_PORT`; `--no-browser` is forwarded as `CL_RUNTIME_NO_BROWSER=1`.
- In REPL mode, stdout and stderr are redirected to the log file (stderr merged via `subprocess.STDOUT`). In CLI mode they are inherited.

---

### `init` -- Project Scaffold Wizard

Interactive 4-page wizard that creates a new project from scratch.

```
cl-runtime init [--non-interactive]
```

| Option | Description |
|--------|-------------|
| `--non-interactive` | Skip the wizard, run `init_project()` and `init_type_info()` using the existing `settings.yaml`. |

**Wizard pages (interactive mode):**

| Page | Title | What happens |
|------|-------|--------------|
| 1 | Project Overview | Explains what the wizard will do, asks for confirmation. |
| 2 | Project Details | Prompts for: project name, root package name, database type (`mongo` or `sqlite`), project directory. |
| 3 | Review | Displays a summary, asks for confirmation. |
| 4 | Execute | Writes `settings.yaml`, scaffolds project files, rebuilds the type cache. |

---

### `init-db` -- Initialize Database

Drop and repopulate the database from preload files.

```
cl-runtime init-db [--force]
```

| Option | Description |
|--------|-------------|
| `--force` | Skip the interactive confirmation prompt when dropping a non-empty database. |

---

### `init-type-info` -- Rebuild Type Cache

Scan all configured packages and regenerate `TypeInfo.csv`.

```
cl-runtime init-type-info
```

No options. Creates missing `__init__.py` files and rebuilds the type cache.

---

### `run` -- Execute a Handler Method

Run a handler method synchronously, or submit it as an async task to the Celery queue.

```
cl-runtime run TYPE_NAME METHOD_NAME [options]
```

| Argument / Option | Description |
|-------------------|-------------|
| `TYPE_NAME` | Short type name, e.g. `DataSourceTool`. |
| `METHOD_NAME` | Method name in PascalCase (converted to snake_case internally). |
| `--key KEY` | Record key for instance methods (semicolon-delimited). |
| `--args JSON` | Method arguments as a JSON string. |
| `--async` | Submit as an async Celery task instead of running synchronously. |
| `--output FILE`, `-o FILE` | Write JSON result to a file instead of stdout. |

---

### `fix-copyright-headers` -- Check/Fix Copyright Headers

```
cl-runtime fix-copyright-headers [--fix]
```

Check and optionally fix Apache 2.0 license headers in source files.

---

### `fix-csv-quotes` -- Fix CSV Quoting

```
cl-runtime fix-csv-quotes
```

Fix CSV quoting issues in all package directories.

---

## CLI Extensions

Downstream applications can add custom CLI commands by subclassing `CliCommand` in any package listed in `package_source_dirs`, then running `init-type-info` to rebuild the type cache.

```python
# myapp/cl/myapp/cli/deploy_cmd.py
import click
from dataclasses import dataclass
from cl.runtime.cli.cli_command import CliCommand

@dataclass(slots=True, kw_only=True)
class DeployCmd(CliCommand):
    @classmethod
    def click_command(cls) -> click.BaseCommand:
        @click.command()
        @click.option("--target", help="Deployment target")
        def deploy(target):
            """Deploy the application."""
            from cl.myapp.deploy import do_deploy
            do_deploy(target)
        return deploy
```

After `cl-runtime init-type-info`, the command is available as `cl-runtime deploy --target production` or `/deploy --target staging` in the REPL.

**How it works:** `CliCommand` inherits from `DataclassMixin`, so `init-type-info` registers all subclasses in `TypeInfo.csv`. At CLI startup, `PluginGroup` lazily calls `discover_cli_plugins()`, which reads `TypeInfo.csv`, imports each subclass, and registers its Click command. Built-in commands take priority; plugin errors are logged as warnings.

---

## Implementation Details

### Built-in Commands

| Class | Module | Click name | Type |
|-------|--------|------------|------|
| `BackendCmd` | `backend_cmd.py` | `backend` | group |
| `InitCmd` | `init_cmd.py` | `init` | command |
| `InitDbCmd` | `init_db_cmd.py` | `init-db` | command |
| `InitTypeInfoCmd` | `init_type_info_cmd.py` | `init-type-info` | command |
| `RunCmd` | `run_cmd.py` | `run` | command |
| `FixCopyrightHeadersCmd` | `fix_copyright_headers_cmd.py` | `fix-copyright-headers` | command |
| `FixCsvQuotesCmd` | `fix_csv_quotes_cmd.py` | `fix-csv-quotes` | command |

Each module exports a module-level alias (e.g. `backend = BackendCmd.click_command()`) for `_standalone.py` and `if __name__ == "__main__"` blocks.

### Package Structure

```
runtime/cl/runtime/cli/
    __init__.py              # Re-exports the cli group
    __main__.py              # Entry point for python -m cl.runtime.cli
    _standalone.py           # Bootstrap helper for direct module invocation
    main.py                  # Click group definition, subcommand registration
    repl.py                  # Interactive REPL loop, autocompletion, key bindings
    bootstrap_util.py        # Shared helpers: apply_env_config(), activate_data_source()
    cli_command.py           # CliCommand base class
    plugin_discovery.py      # Plugin discovery and PluginGroup
    backend_cmd.py           # BackendCmd -- server lifecycle (start/stop/status/log)
    init_cmd.py              # InitCmd -- project scaffold wizard
    init_db_cmd.py           # InitDbCmd -- database initialization
    init_type_info_cmd.py    # InitTypeInfoCmd -- type cache rebuild
    run_cmd.py               # RunCmd -- handler execution (sync + async)
    fix_copyright_headers_cmd.py  # FixCopyrightHeadersCmd
    fix_csv_quotes_cmd.py    # FixCsvQuotesCmd
```

### Invocation Paths

There are three distinct invocation paths with different bootstrap sequences:

**`python -m cl.runtime.cli`** (source tree): `__main__.py` pre-parses `--env` from `sys.argv`, sets `CL_SETTINGS_ENV`, calls `locate.append_sys_path`, imports bootstrap, then calls `cli()`.

**`python -m cl.runtime.cli.<command_module>`** (direct module): `_standalone.py:run_command()` pre-parses and strips `--env`, runs bootstrap if needed, configures logging, then invokes the Click command.

**`cl-runtime`** (console script): The `[project.scripts]` entry point calls `cli()` directly. The group callback checks `sys.modules` for bootstrap and runs it if missing. Heavy imports happen lazily inside each subcommand.

### Bootstrap Timing

The `--env` option must be parsed **before** `cl.runtime.bootstrap` is imported because bootstrap triggers `PackageSettings.instance()` which reads Dynaconf settings using `CL_SETTINGS_ENV`.

### Lazy Import Strategy

All subcommand modules use lazy imports (inside function bodies) for anything beyond `click`, `os`, and standard library modules. This is necessary because `tools.*` modules are only on `sys.path` after bootstrap, and `cl.runtime.*` modules that depend on Dynaconf settings trigger initialization at import time.

### Context Activation Patterns

| Command | Contexts Activated |
|---------|-------------------|
| `init`, `init-type-info` | None (tool functions handle their own) |
| `init-db` | `DataSource` (internal) |
| `run` (sync) | `Env` + `DataSource` |
| `run` (async) | `Env` + `DataSource` + `EventBroker` |
| `fix-*` | None |
| `backend` | None (subprocess activates its own contexts) |
