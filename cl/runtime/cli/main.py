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

import logging.config
import sys
import click
from cl.runtime.cli.plugin_discovery import discover_cli_plugins
from cl.runtime.cli.plugin_discovery import PluginGroup


@click.group(invoke_without_command=True, cls=PluginGroup)
@click.option("--env", default=None, help="Dynaconf environment name (e.g. development, staging, etc.).")
@click.version_option(package_name="cl-runtime")
@click.pass_context
def cli(ctx: click.Context, env: str | None) -> None:
    """CompatibL Runtime CLI."""

    # Ensure bootstrap is loaded when invoked via console script entry point
    if "cl.runtime.bootstrap" not in sys.modules:
        import locate

        locate.append_sys_path("../../..")

        import cl.runtime.bootstrap  # noqa: F401 isort: skip

    # Apply environment configuration and set up logging
    from cl.runtime.cli.bootstrap_util import apply_env_config
    from cl.runtime.log.log_config import logging_config

    apply_env_config(env)
    logging.config.dictConfig(logging_config)

    # Store env in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["env"] = env

    # Discover plugin commands (idempotent, handles console-script path)
    discover_cli_plugins(cli)

    # If no subcommand was given, launch the interactive REPL
    if ctx.invoked_subcommand is None:
        from cl.runtime.cli.repl import register_commands
        from cl.runtime.cli.repl import run_repl

        register_commands(cli)
        run_repl(ctx)


# Import and register subcommands (lazy click command objects are lightweight)
from cl.runtime.cli.backend_cmd import BackendCmd  # noqa: E402
from cl.runtime.cli.fix_copyright_headers_cmd import FixCopyrightHeadersCmd  # noqa: E402
from cl.runtime.cli.fix_csv_quotes_cmd import FixCsvQuotesCmd  # noqa: E402
from cl.runtime.cli.init_cmd import InitCmd  # noqa: E402
from cl.runtime.cli.init_db_cmd import InitDbCmd  # noqa: E402
from cl.runtime.cli.init_type_info_cmd import InitTypeInfoCmd  # noqa: E402
from cl.runtime.cli.run_cmd import RunCmd  # noqa: E402

cli.add_command(BackendCmd.click_command())
cli.add_command(InitCmd.click_command())
cli.add_command(InitDbCmd.click_command())
cli.add_command(InitTypeInfoCmd.click_command())
cli.add_command(RunCmd.click_command())
cli.add_command(FixCopyrightHeadersCmd.click_command())
cli.add_command(FixCsvQuotesCmd.click_command())
