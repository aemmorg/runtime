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

from collections import defaultdict
from dataclasses import dataclass
from itertools import chain
from typing import Sequence
from more_itertools import consume
from typing_extensions import final
from cl.runtime.configurations.configuration import Configuration
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.file.csv_reader import CsvReader
from cl.runtime.file.json_reader import JsonReader
from cl.runtime.file.jsonl_reader import JsonlReader
from cl.runtime.file.excel_reader import ExcelReader
from cl.runtime.file.yaml_reader import YamlReader
from cl.runtime.settings.preload_settings import PreloadSettings


@dataclass(slots=True, kw_only=True)
@final
class PreloadConfiguration(Configuration):
    """Settings for preloading records from files."""

    dirs: Sequence[str] | None = None
    """Directories where file search is performed."""

    file_include_patterns: Sequence[str] | None = None
    """Optional list of filename glob patterns to include."""

    file_exclude_patterns: Sequence[str] | None = None
    """Optional list of filename glob patterns to exclude"""

    def run_configure(self):
        """Load records from files in the specified directories and insert them into the active data source."""

        # Ensure that DB in the active data source is empty, not considering parents
        if not (ds := active(DataSource)).is_empty(consider_parents=False):
            raise RuntimeError(
                f"PreloadConfiguration requires an empty DB in the active data source (not considering parents),\n"
                f"but found that DB '{ds.get_db_id()}' is not empty."
            )

        # Use preload_dirs if dirs field is None
        preload_settings = PreloadSettings.instance()
        dirs = self.dirs or preload_settings.preload_dirs

        # Convert XLSX files to CSV before loading
        ExcelReader.convert_to_csv(
            dirs=dirs,
            ext="xlsx",
            file_include_patterns=self.file_include_patterns,
            file_exclude_patterns=self.file_exclude_patterns,
        )

        # Fix CSV files on disk before loading to ensure DB gets data in the correct format
        CsvReader.check_or_fix_format(
            dirs=dirs,
            ext="csv",
            fix=True,
            file_include_patterns=self.file_include_patterns,
            file_exclude_patterns=self.file_exclude_patterns,
        )

        # Specify readers for each file extension
        reader_dict = {
            "csv": CsvReader().build(),
            "json": JsonReader().build(),
            "jsonl": JsonlReader().build(),
            "yaml": YamlReader().build(),
        }

        # Load records from preload directories, each reader returns frozendict[str, tuple[RecordMixin, ...]]
        result_dicts = [
            reader.load_all(
                dirs=dirs,
                ext=ext,
                file_include_patterns=self.file_include_patterns,
                file_exclude_patterns=self.file_exclude_patterns,
            )
            for ext, reader in reader_dict.items()
        ]

        # Merge records by dataset across all readers
        records_by_dataset: dict[str, list] = defaultdict(list)
        for result_dict in result_dicts:
            for dataset, records in result_dict.items():
                records_by_dataset[dataset].extend(records)

        if records_by_dataset:
            # Validate dataset format and save each group with the appropriate dataset
            all_records = list(chain.from_iterable(records_by_dataset.values()))
            for dataset, group_records in records_by_dataset.items():
                if not dataset.startswith("\\"):
                    raise RuntimeError(
                        f"Dataset identifier '{dataset}' must begin with a backslash character."
                    )
                temp_ds = DataSource(db=ds.db, datasets=[dataset], tenant=ds.tenant).build()
                temp_ds.insert_many(group_records, commit=True)

            # Execute run_configure on all preloaded Configuration records with autorun=True
            autorun_configurations = [
                record for record in all_records if isinstance(record, Configuration) and record.autorun
            ]

            # Execute their run_configure methods
            consume(autorun_configuration.run_configure() for autorun_configuration in autorun_configurations)
