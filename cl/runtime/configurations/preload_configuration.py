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
from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence
from more_itertools import consume
from typing_extensions import final
from cl.runtime.configurations.configuration import Configuration
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.dataset_util import DatasetUtil
from cl.runtime.file.csv_reader import CsvReader
from cl.runtime.file.file_util import FileUtil
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

        # Collect records grouped by dataset across all preload dirs and file extensions
        records_by_dataset = defaultdict(list)
        for preload_dir in dirs:
            for ext, reader in reader_dict.items():
                abs_paths = FileUtil.enumerate_files(
                    dirs=[preload_dir],
                    ext=ext,
                    file_include_patterns=self.file_include_patterns,
                    file_exclude_patterns=self.file_exclude_patterns,
                )
                for abs_path in abs_paths:
                    # Get relative path from preload dir to compute dataset
                    relative_path = os.path.relpath(abs_path, preload_dir).replace(os.sep, "/")
                    dir_part = os.path.dirname(relative_path)
                    # Convert directory part to dataset: empty dir_part maps to root dataset "/"
                    dataset = DatasetUtil.root() if not dir_part else "/" + dir_part
                    # Load records from the file
                    records = reader.load_file(file_path=abs_path)
                    records_by_dataset[dataset].extend(records)

        # Save original datasets to restore after preloading
        original_datasets = ds.datasets

        # Collect all autorun configurations across all datasets
        all_autorun_configurations = []

        try:
            # Insert records for each dataset
            for dataset, records in records_by_dataset.items():
                if records:
                    ds.datasets = [dataset]
                    ds.insert_many(records, commit=True)

                    # Collect autorun configurations
                    all_autorun_configurations.extend(
                        record for record in records if isinstance(record, Configuration) and record.autorun
                    )
        finally:
            # Restore original datasets
            ds.datasets = original_datasets

        # Execute run_configure on all preloaded Configuration records with autorun=True
        consume(autorun_configuration.run_configure() for autorun_configuration in all_autorun_configurations)
