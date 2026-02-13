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

from dataclasses import dataclass
import click
from cl.runtime.cli.cli_command import CliCommand


@dataclass(slots=True, kw_only=True)
class InitDbCmd(CliCommand):
    """CLI command to initialize the database (drop and repopulate from preloads)."""

    @classmethod
    def click_command(cls) -> click.BaseCommand:
        """Return the Click command to register on the CLI group."""

        @click.command("init-db")
        @click.option(
            "--force", is_flag=True, default=False, help="Skip interactive approval when dropping a non-empty DB."
        )
        def init_db(force: bool) -> None:
            """Initialize the database (drop and repopulate from preloads)."""
            from tools.cl.runtime.init_db import init_db as _init_db

            _init_db(interactive=not force)

        return init_db


init_db = InitDbCmd.click_command()


if __name__ == "__main__":
    from cl.runtime.cli._standalone import run_command

    run_command(init_db)
