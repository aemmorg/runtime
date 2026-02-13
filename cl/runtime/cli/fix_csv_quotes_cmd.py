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
class FixCsvQuotesCmd(CliCommand):
    """CLI command to fix CSV quoting issues in project files."""

    @classmethod
    def click_command(cls) -> click.BaseCommand:
        """Return the Click command to register on the CLI group."""

        @click.command("fix-csv-quotes")
        def fix_csv_quotes() -> None:
            """Fix CSV quoting in all package directories."""
            from cl.runtime.file.csv_reader import CsvReader
            from cl.runtime.project.project_layout import ProjectLayout
            from cl.runtime.settings.package_settings import PackageSettings

            packages = PackageSettings.instance().get_packages()

            dirs = set()
            for package in packages:
                if (x := ProjectLayout.get_package_source_root(package)) is not None and x not in dirs:
                    dirs.add(x)
                if (x := ProjectLayout.get_package_stubs_root(package)) is not None and x not in dirs:
                    dirs.add(x)
                if (x := ProjectLayout.get_package_tests_root(package)) is not None and x not in dirs:
                    dirs.add(x)
                if (x := ProjectLayout.get_package_preloads_root(package)) is not None and x not in dirs:
                    dirs.add(x)

            CsvReader.check_or_fix_quotes(
                dirs=tuple(dirs),
                ext="csv",
                apply_fix=True,
                verbose=True,
                file_exclude_patterns=[
                    "unescaped_date.csv",
                    "unescaped_float.csv",
                ],
            )

        return fix_csv_quotes


fix_csv_quotes = FixCsvQuotesCmd.click_command()


if __name__ == "__main__":
    from cl.runtime.cli._standalone import run_command

    run_command(fix_csv_quotes)
