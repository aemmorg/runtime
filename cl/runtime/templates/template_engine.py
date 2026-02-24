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

import platform
import posixpath
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Mapping
from jinja2 import Environment
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.protocols import is_mapping_type
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typenameof
from cl.runtime.records.typename import typeof
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.templates.template_engine_key import TemplateEngineKey

_JINJA_ENV_FOR_PATH = Environment(
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)
"""Jinja environment for variable substitution in directories and paths, strips whitespace."""


def transform_part(part: str) -> str:
    """Replace dot_ prefix by . in file or directory name token."""
    return "." + part.removeprefix("dot_") if part.startswith("dot_") else part


@dataclass(slots=True, kw_only=True)
class TemplateEngine(TemplateEngineKey, RecordMixin, ABC):
    """Engine to perform template rendering."""

    def get_key(self) -> TemplateEngineKey:
        return TemplateEngineKey(engine_id=self.engine_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.engine_id is None:
            # Use globally unique UUIDv7-based timestamp if not specified
            self.engine_id = Timestamp.create()

    @abstractmethod
    def render(self, *, body: str, data: DataMixin | Mapping[str, Any]) -> str:
        """Render the template body by taking parameters from a data object or a mapping."""

    def render_dir(
        self,
        *,
        template_dir: str,
        output_dir: str,
        data: DataMixin | Mapping[str, Any],
        force: bool = False,
    ) -> None:
        """
        Render all templates with filename.ext.j2 name in input_dir and its subdirectories by taking parameters
        from data object or dict, write output to filename.ext in the matching subdirectory of output_dir,
        performing f-string variable substitution in filename or directory.

        Args:
            template_dir: Directory containing templates (may include subdirectories)
            output_dir: Output directory (subdirectories will be created)
            data: Data for Jinja2 parameter substitution
            force: If True, overwrite files even if they already exist
        """

        # Find all .j2 files recursively in input_dir
        template_files = list(Path(template_dir).rglob("*.j2"))

        # Process each template file
        for template_file in template_files:

            # Render and apply filters to the relative path relative to template_dir
            rel_path = str(template_file.relative_to(template_dir))

            # Use Jinja2 engine to render variables in relative path
            if "{" in rel_path:
                # Render using Jinja2 if double braces are in path
                if "{{" in rel_path:
                    # Use default serializer to convert to a mapping with string leaf values
                    data_dict = DataSerializers.DEFAULT.serialize(data)
                    if is_mapping_type(typeof(data_dict)):
                        rel_path = _JINJA_ENV_FOR_PATH.from_string(rel_path).render(data_dict)
                    else:
                        # Error if not a mapping after serialization
                        raise RuntimeError(
                            f"Param 'data' in {typenameof(self)}.render(template, data) must be\n"
                            f"a data object derived from DataMixin or a mapping."
                        )
                else:
                    # Error if only a single brace
                    raise RuntimeError(
                        "Filename or directory path contains a single brace '{ var }',\n"
                        "replace by two braces '{{ var }}' for Jinja2 substitution:\n" + str(rel_path)
                    )

            # Render dot_ as . in the beginning of file and directory names but not in other locations
            rel_path = posixpath.normpath(rel_path).replace("/dot_", "/.").replace("dot_", ".")

            # Remove trailing .j2 suffix if present
            rel_path = rel_path.removesuffix(".j2")

            # Create output directory if it doesn't exist
            output_file = Path(output_dir) / rel_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Read template file content and render
            template_text = template_file.read_text(encoding="utf-8")
            content = self.render(body=template_text, data=data)

            # Normalize content to use LF, then let Python convert based on newline parameter
            # Replace any existing CRLF or CR with LF
            content = content.replace("\r\n", "\n").replace("\r", "\n")

            # Use CRLF on Windows, LF on Linux
            newline_char = "\r\n" if platform.system() == "Windows" else "\n"
            if force or not output_file.exists():
                # Write rendered content with OS-appropriate line endings
                with open(output_file, "w", encoding="utf-8", newline=newline_char) as f:
                    f.write(content)
