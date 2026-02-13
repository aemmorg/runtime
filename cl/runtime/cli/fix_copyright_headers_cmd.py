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
class FixCopyrightHeadersCmd(CliCommand):
    """CLI command to check and fix copyright headers in source files."""

    @classmethod
    def click_command(cls) -> click.BaseCommand:
        """Return the Click command to register on the CLI group."""

        @click.command("fix-copyright-headers")
        @click.option("--fix", is_flag=True, default=False, help="Automatically fix missing/incorrect copyright headers.")
        def fix_copyright_headers(fix: bool) -> None:
            """Check (and optionally fix) copyright headers."""
            from cl.runtime.prebuild.copyright_util import CopyrightUtil

            CopyrightUtil.check_copyright_headers(fix_header=fix, fix_trailing_blank_line=True, verbose=True)

        return fix_copyright_headers


fix_copyright_headers = FixCopyrightHeadersCmd.click_command()


if __name__ == "__main__":
    from cl.runtime.cli._standalone import run_command

    run_command(fix_copyright_headers)
