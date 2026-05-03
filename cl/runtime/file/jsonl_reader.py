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
from typing import Any
from typing import Sequence
import orjson
from frozendict import frozendict
from cl.runtime.file.file_util import FileUtil
from cl.runtime.file.reader import Reader
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.data_serializers import DataSerializers

_SERIALIZER = DataSerializers.FOR_JSON


@dataclass(slots=True, kw_only=True)
class JsonlReader(Reader):
    """Load records from JSONL (JSON Lines) files into the context database."""

    def load_file(self, *, file_path: str) -> frozendict[str, tuple[RecordMixin, ...]]:
        """Load records from a single JSONL file grouped by dataset."""

        records_by_dataset: dict[str, list[RecordMixin]] = defaultdict(list)
        try:
            record_type = FileUtil.get_type_from_filename(file_path, raise_on_fail=False)

            with open(file_path, mode="rb") as file:
                data = file.read().strip()

                if not data:
                    return frozendict()

                # Parse all lines in a single orjson call by wrapping as a JSON array
                non_empty_lines = [line for line in data.split(b"\n") if line.strip()]
                json_bytes = b"[" + b",".join(non_empty_lines) + b"]"
                object_dicts = orjson.loads(json_bytes)

                invalid_objects = {
                    index
                    for index, object_dict in enumerate(object_dicts)
                    for key in object_dict.keys()
                    if key is None or key == ""
                }

                if invalid_objects:
                    rows_str = "".join([f"Row: {invalid_object}\n" for invalid_object in invalid_objects])
                    raise RuntimeError(
                        "Misaligned values found in the following objects.\n"
                        "Check the placement of commas, brackets and double quotes.\n" + rows_str
                    )

                for object_dict in object_dicts:
                    record, dataset = self._deserialize_object(record_type=record_type, object_dict=object_dict)
                    records_by_dataset[dataset or "/"].append(record)
        except Exception as e:
            raise RuntimeError(f"Failed to load JSONL file {file_path}.\n" f"Error: {e}") from e

        return frozendict({k: tuple(v) for k, v in records_by_dataset.items()})

    @classmethod
    def check_or_fix_file(cls, file_path: str, *, fix: bool) -> bool:
        """Check and optionally fix formatting in a single JSONL file.

        Each line is re-encoded with orjson.dumps() to produce compact, canonical JSON.

        Args:
            file_path: Path to the JSONL file to check or fix
            fix: If True, overwrite the file with fixed values; if False, only check
        Returns:
            True if the file is already valid, False if changes are needed
        """

        with open(file_path, "rb") as f:
            original_bytes = f.read()

        # Normalize line endings to \n before comparison
        normalized_bytes = original_bytes.replace(b"\r\n", b"\n")
        lines = normalized_bytes.split(b"\n")
        canonical_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                canonical_lines.append(b"")
                continue
            obj = orjson.loads(stripped)
            canonical_lines.append(orjson.dumps(obj))

        canonical_bytes = b"\n".join(canonical_lines)

        is_valid = normalized_bytes == canonical_bytes
        if fix and not is_valid:
            with open(file_path, "wb") as f:
                f.write(canonical_bytes)
        return is_valid

    @classmethod
    def check_or_fix_format(
        cls,
        *,
        dirs: Sequence[str],
        ext: str,
        fix: bool,
        verbose: bool = False,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> None:
        """Check and optionally fix all JSONL format issues in a single pass.

        Args:
            dirs: Directories where file search is performed
            ext: File extension to search for without the leading dot (e.g., "jsonl")
            fix: If True, fix all format issues; if False, only check and report
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        file_paths = FileUtil.enumerate_files(
            dirs=dirs,
            ext=ext,
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        files_with_error = []
        for file_path in file_paths:
            is_valid = cls.check_or_fix_file(file_path, fix=fix)
            if not is_valid:
                files_with_error.append(file_path)

        if files_with_error:
            files_list = "".join([f"    {file}\n" for file in files_with_error])
            if not fix:
                raise RuntimeError(
                    f"Found JSONL format issues in these files.\n"
                    f"Recommended action: run fix script to fix.\n{files_list}"
                )
            elif verbose:
                print(f"Corrected JSONL format in the following files:\n{files_list}")
        elif verbose:
            files_list = "".join([f"    {x}\n" for x in sorted(file_paths)])
            print(f"Verified JSONL format in the following files:\n{files_list}")

    @classmethod
    def _deserialize_object(cls, *, record_type: type | None, object_dict: dict[str, Any]) -> tuple[RecordMixin, str | None]:
        """Deserialize JSON object into a record with optional dataset.
        Args:
            record_type: Record type hint derived from filename, or None if not available.
            object_dict: Dictionary representing the JSON object.
        Returns:
            Tuple of (deserialized record, dataset string or None).
        Raises:
            RuntimeError: If record type cannot be determined or deserialization fails.
        """

        # First, check if _type is provided in the JSON object
        if "_type" in object_dict:
            record_type_name = object_dict["_type"]

            try:
                record_type = TypeInfo.from_type_name(record_type_name)
            except Exception as e:
                raise RuntimeError(
                    f"Could not determine record type '{record_type_name}'from JSON '_type'. Provide a valid type.\n"
                    f"Error: {e}"
                )

        # If record_type is still None, we cannot determine the type
        if record_type is None:
            raise RuntimeError(
                "Could not determine record type: "
                "JSON '_type' is missing/invalid and filename-derived type not available."
            )

        # Extract _dataset before deserialization (not a record field)
        dataset = object_dict.pop("_dataset", None)

        # Ensure _type is set for deserialization
        object_dict["_type"] = typename(record_type)

        result = _SERIALIZER.deserialize(object_dict).build()
        return result, dataset
