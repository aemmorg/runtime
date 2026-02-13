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
class InitTypeInfoCmd(CliCommand):
    """CLI command to rebuild the type cache (TypeInfo.csv)."""

    @classmethod
    def click_command(cls) -> click.BaseCommand:
        """Return the Click command to register on the CLI group."""

        @click.command("init-type-info")
        def init_type_info() -> None:
            """Rebuild the type cache (TypeInfo.csv)."""
            from tools.cl.runtime.init_type_info import init_type_info as _init_type_info

            _init_type_info()

        return init_type_info


init_type_info = InitTypeInfoCmd.click_command()


if __name__ == "__main__":
    from cl.runtime.cli._standalone import run_command

    run_command(init_type_info)
