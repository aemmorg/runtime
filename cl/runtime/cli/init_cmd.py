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
from dataclasses import dataclass
import click
from cl.runtime.cli.cli_command import CliCommand
from ruamel.yaml import YAML

_DB_CHOICES = {
    "mongo": {"db_type": "BasicMongoDb", "db_mongo_uri": "mongodb://localhost:27017/"},
    "sqlite": {"db_type": "SqliteDb"},
}


@dataclass(slots=True, kw_only=True)
class InitCmd(CliCommand):
    """CLI command to initialize a new project (interactive wizard)."""

    @classmethod
    def click_command(cls) -> click.BaseCommand:
        """Return the Click command to register on the CLI group."""

        @click.command()
        @click.option(
            "--non-interactive",
            is_flag=True,
            default=False,
            help="Skip the interactive wizard and use defaults or existing settings.",
        )
        def init(non_interactive: bool) -> None:
            """Initialize a new project (interactive wizard)."""
            if non_interactive:
                _run_non_interactive()
            else:
                _run_wizard()

        return init


init = InitCmd.click_command()


def _run_wizard() -> None:
    """Run the 4-page interactive project scaffold wizard."""

    # Page 1: Project Overview
    click.echo()
    click.echo("=" * 60)
    click.echo("  CompatibL Runtime - Project Initialization Wizard")
    click.echo("=" * 60)
    click.echo()
    click.echo("This wizard will:")
    click.echo("  1. Collect project configuration details")
    click.echo("  2. Generate settings.yaml with your configuration")
    click.echo("  3. Scaffold project files from templates")
    click.echo("  4. Rebuild the type cache (TypeInfo.csv)")
    click.echo()
    if not click.confirm("Continue?", default=True):
        click.echo("Aborted.")
        return

    # Page 2: Project Details
    click.echo()
    click.echo("-" * 60)
    click.echo("  Project Details")
    click.echo("-" * 60)
    click.echo()

    project_name = click.prompt("Project name", default="my-project")
    root_package = click.prompt("Root package name", default="cl.myapp")
    db_type = click.prompt(
        "Database type", type=click.Choice(list(_DB_CHOICES.keys()), case_sensitive=False), default="mongo"
    )
    project_dir = click.prompt("Project directory", default=os.getcwd(), type=click.Path())

    # Page 3: Review
    click.echo()
    click.echo("-" * 60)
    click.echo("  Review Configuration")
    click.echo("-" * 60)
    click.echo()
    click.echo(f"  Project name:    {project_name}")
    click.echo(f"  Root package:    {root_package}")
    click.echo(f"  Database type:   {db_type}")
    click.echo(f"  Project dir:     {project_dir}")
    click.echo()
    if not click.confirm("Proceed with these settings?", default=True):
        click.echo("Aborted.")
        return

    # Page 4: Execute
    click.echo()
    click.echo("-" * 60)
    click.echo("  Initializing Project")
    click.echo("-" * 60)
    click.echo()

    _write_settings_yaml(project_dir, project_name, root_package, db_type)
    _run_scaffold_and_type_info()

    click.echo()
    click.echo("Project initialization complete.")


def _run_non_interactive() -> None:
    """Run project initialization without the wizard using defaults or existing settings."""
    click.echo("Running project initialization with existing settings...")
    _run_scaffold_and_type_info()
    click.echo("Project initialization complete.")


def _write_settings_yaml(project_dir: str, project_name: str, root_package: str, db_type: str) -> None:
    """Write settings.yaml with the collected configuration."""
    db_settings = _DB_CHOICES[db_type]

    # Build package_source_dirs from root_package
    package_source_dirs = {"cl.runtime": "runtime", root_package: project_name}

    settings = {
        "default": {
            "env_id": f"Dev{project_name.replace('-', '').title()}Main",
            "env_kind": "DEV",
            "env_tenant": "temp_tenant",
            "package_source_dirs": package_source_dirs,
            "db_id": f"temp_{project_name.replace('-', '_')}_main",
            **db_settings,
            "api_hostname": "localhost",
            "api_port": 7008,
            "api_allow_origins": [
                "http://localhost:3005",
                "http://127.0.0.1:3005",
                "http://localhost:10000",
            ],
            "api_allow_credentials": True,
            "api_allow_methods": ["*"],
            "api_allow_headers": ["*"],
            "auth_enabled": False,
        }
    }

    settings_path = os.path.join(project_dir, "settings.yaml")
    yaml = YAML()
    yaml.default_flow_style = False
    with open(settings_path, "w", encoding="utf-8") as f:
        yaml.dump(settings, f)
    click.echo(f"  Written {settings_path}")


def _run_scaffold_and_type_info() -> None:
    """Run init_project and init_type_info tools."""
    from tools.cl.runtime.init_project import init_project
    from tools.cl.runtime.init_type_info import init_type_info

    click.echo("  Scaffolding project files...")
    init_project()

    click.echo("  Rebuilding type cache...")
    init_type_info()


if __name__ == "__main__":
    from cl.runtime.cli._standalone import run_command

    run_command(init)
