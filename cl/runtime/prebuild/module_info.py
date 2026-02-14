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

import hashlib
import os
from cl.runtime.project.project_layout import ProjectLayout

_MODULE_INFO_HEADERS = ("RelPath", "SHA256")
"""Headers of ModuleInfo preload file."""


class ModuleInfo:
    """Utility for computing and comparing source file hashes to detect changes."""

    @classmethod
    def compute_file_hash(cls, file_path: str) -> str:
        """Compute SHA-256 hash of raw file bytes."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @classmethod
    def compute_hashes(cls, file_paths: list[str]) -> dict[str, str]:
        """Compute SHA-256 hashes for a list of absolute file paths.

        Returns:
            Dictionary mapping relative path (forward-slash, relative to project root) to hex hash.
        """
        project_root = ProjectLayout.get_project_root()
        result = {}
        for abs_path in file_paths:
            rel_path = os.path.relpath(abs_path, project_root).replace(os.sep, "/")
            result[rel_path] = cls.compute_file_hash(abs_path)
        return result

    @classmethod
    def load(cls) -> dict[str, str] | None:
        """Load ModuleInfo.csv from the bootstrap resources directory.

        Returns:
            Dictionary mapping relative path to hex hash, or None if the file does not exist or is corrupt.
        """
        filename = cls._get_filename()
        if not os.path.exists(filename):
            return None

        result = {}
        with open(filename, "r", encoding="utf-8") as f:
            for line_index, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                if line_index == 0:
                    tokens = tuple(x.strip() for x in line.split(","))
                    if tokens != _MODULE_INFO_HEADERS:
                        return None
                    continue
                parts = line.split(",", 1)
                if len(parts) == 2:
                    result[parts[0].strip()] = parts[1].strip()
        return result

    @classmethod
    def save(cls, hashes: dict[str, str]) -> None:
        """Save ModuleInfo.csv to the bootstrap resources directory."""
        filename = cls._get_filename()
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(",".join(_MODULE_INFO_HEADERS) + "\n")
            for rel_path in sorted(hashes.keys()):
                f.write(f"{rel_path},{hashes[rel_path]}\n")

    @classmethod
    def has_changes(cls, current_hashes: dict[str, str]) -> bool:
        """Compare current hashes against saved ModuleInfo.csv.

        Returns:
            True if changes are detected (or if ModuleInfo.csv is missing), False if all hashes match.
        """
        saved_hashes = cls.load()
        if saved_hashes is None:
            return True
        return current_hashes != saved_hashes

    @classmethod
    def _get_filename(cls) -> str:
        """Get the filename for ModuleInfo.csv."""
        resources_root = ProjectLayout.get_resources_root()
        return os.path.join(resources_root, "bootstrap/ModuleInfo.csv")
