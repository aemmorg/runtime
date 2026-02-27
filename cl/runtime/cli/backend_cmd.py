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

import atexit
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
import click
from cl.runtime.cli.cli_command import CliCommand

# ---------------------------------------------------------------------------
# Backend process state
# ---------------------------------------------------------------------------

_backend_process: subprocess.Popen | None = None
_backend_port: int | None = None
_backend_log_path: str | None = None
_backend_log_file = None  # open file handle for the log


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def _build_backend_env(port: int | None = None, no_browser: bool = False) -> dict[str, str]:
    """Build environment dict for the backend subprocess."""
    env = os.environ.copy()
    if port is not None:
        env["CL_API_PORT"] = str(port)
    if no_browser:
        env["CL_RUNTIME_NO_BROWSER"] = "1"
    return env


def _launch_backend(
    port: int | None = None,
    no_browser: bool = False,
    *,
    stdout=None,
    stderr=None,
) -> subprocess.Popen:
    """Launch the backend server as a subprocess and return the Popen handle.

    *stdout* and *stderr* are forwarded to ``subprocess.Popen``.  When ``None``
    (the default) the child inherits the parent's streams, preserving the
    existing CLI behaviour.  The REPL passes a log file so that server output
    does not garble the interactive prompt.
    """
    env = _build_backend_env(port, no_browser)
    return subprocess.Popen([sys.executable, "-m", "cl.runtime"], env=env, stdout=stdout, stderr=stderr)


def _resolve_display_port(port: int | None) -> int:
    """Return the port number to display in status messages."""
    if port is not None:
        return port
    try:
        from cl.runtime.settings.api_settings import ApiSettings

        settings = ApiSettings.instance()
        return settings.api_port
    except Exception:
        return 7008


# ---------------------------------------------------------------------------
# Process management (used by subcommands and the REPL atexit handler)
# ---------------------------------------------------------------------------


def _start_backend(port: int | None = None, no_browser: bool = False, *, repl: bool = False) -> None:
    """Start the backend server.  In REPL mode it runs in the background with log redirection."""
    global _backend_process, _backend_port, _backend_log_path, _backend_log_file

    if repl:
        if _backend_process is not None and _backend_process.poll() is None:
            click.echo(f"Backend already running (PID {_backend_process.pid}). Use /backend stop first.")
            return

        _backend_log_path = os.path.join(tempfile.gettempdir(), "cl_runtime_backend.log")
        _backend_log_file = open(_backend_log_path, "w")  # noqa: SIM115

        _backend_process = _launch_backend(
            port=port,
            no_browser=no_browser,
            stdout=_backend_log_file,
            stderr=subprocess.STDOUT,
        )
        _backend_port = port
        atexit.register(cleanup_backend)
        display_port = _resolve_display_port(port)
        click.echo(
            f"Backend started (PID {_backend_process.pid}) on http://localhost:{display_port}"
            f" \u2014 log: {_backend_log_path}"
        )
    else:
        proc = _launch_backend(port=port, no_browser=no_browser)
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        raise SystemExit(proc.returncode or 0)


def _stop_backend() -> None:
    """Terminate the background backend process if running."""
    global _backend_process, _backend_port, _backend_log_file

    if _backend_process is None or _backend_process.poll() is not None:
        click.echo("No backend process is running.")
        _backend_process = None
        _backend_port = None
        return

    pid = _backend_process.pid
    _backend_process.terminate()
    try:
        _backend_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _backend_process.kill()
        _backend_process.wait()
    # Close log file handle but keep _backend_log_path so /backend log still works
    if _backend_log_file is not None:
        _backend_log_file.close()
        _backend_log_file = None
    click.echo(f"Backend (PID {pid}) stopped.")
    _backend_process = None
    _backend_port = None


def cleanup_backend() -> None:
    """Silently terminate the backend process.  Used as atexit handler and REPL finally block."""
    global _backend_process, _backend_log_file
    if _backend_process is None:
        return
    if _backend_process.poll() is not None:
        _backend_process = None
        if _backend_log_file is not None:
            _backend_log_file.close()
            _backend_log_file = None
        return
    _backend_process.terminate()
    try:
        _backend_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _backend_process.kill()
        _backend_process.wait()
    _backend_process = None
    if _backend_log_file is not None:
        _backend_log_file.close()
        _backend_log_file = None


def _show_status() -> None:
    """Print the current backend process status."""
    if _backend_process is not None and _backend_process.poll() is None:
        port_info = f" on port {_backend_port}" if _backend_port else ""
        log_info = f"  log: {_backend_log_path}" if _backend_log_path else ""
        click.echo(f"Backend running (PID {_backend_process.pid}){port_info}{log_info}")
    else:
        click.echo("No backend process is running.")


def _show_log(n: int = 20) -> None:
    """Print the last *n* lines from the backend log file."""
    if _backend_log_path is None or not os.path.isfile(_backend_log_path):
        click.echo("No backend log available. Start the backend first with /backend.")
        return
    with open(_backend_log_path) as f:
        lines = f.readlines()
    total = len(lines)
    tail = lines[-n:] if n < total else lines
    click.echo(f"--- backend log ({len(tail)} of {total} lines) ---")
    for line in tail:
        click.echo(line, nl=False)
    click.echo(f"--- end of log ({_backend_log_path}) ---")


# ---------------------------------------------------------------------------
# Click command group
# ---------------------------------------------------------------------------


@dataclass(slots=True, kw_only=True)
class BackendCmd(CliCommand):
    """CLI command group for the FastAPI/Uvicorn backend server."""

    @classmethod
    def click_command(cls) -> click.BaseCommand:
        """Return the Click group to register on the CLI."""

        @click.group("backend", invoke_without_command=True)
        @click.pass_context
        def backend(ctx: click.Context) -> None:
            """Manage the backend server.

            Without a subcommand, starts the server (same as ``backend start``).
            """
            if ctx.invoked_subcommand is None:
                ctx.invoke(start)

        @backend.command()
        @click.option("--port", default=None, type=int, help="Override the API port from settings.")
        @click.option("--no-browser", is_flag=True, default=False, help="Do not open a browser tab on startup.")
        @click.pass_context
        def start(ctx: click.Context, port: int | None, no_browser: bool) -> None:
            """Start the backend server (foreground in CLI, background in REPL)."""
            is_repl = (ctx.obj or {}).get("repl", False)
            _start_backend(port=port, no_browser=no_browser, repl=is_repl)

        @backend.command()
        def stop() -> None:
            """Stop the running backend server."""
            _stop_backend()

        @backend.command()
        def status() -> None:
            """Show backend server status."""
            _show_status()

        @backend.command()
        @click.argument("lines", default=20, type=int)
        def log(lines: int) -> None:
            """Show recent backend log output (default: last 20 lines)."""
            _show_log(lines)

        return backend


backend = BackendCmd.click_command()


if __name__ == "__main__":
    from cl.runtime.cli._standalone import run_command

    run_command(backend)
