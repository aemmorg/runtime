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
class StubCmd(CliCommand):
    """Stub CLI command for platform minimal samples."""

    @classmethod
    def click_command(cls) -> click.BaseCommand:
        """Return the Click command to register on the CLI group."""

        @click.command("stub")
        @click.option("--name", default="world", help="Name to greet.")
        def stub(name: str) -> None:
            """Stub command that prints a greeting (platform minimal sample)."""
            click.echo(f"Hello, {name}! (stub)")

        return stub
