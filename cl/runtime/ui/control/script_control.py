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
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.ui.control import Control


@dataclass(slots=True, kw_only=True, eq=False)
class ScriptControl(Control):
    """Script editor control with optional syntax highlighting."""

    body: list[str] = required(default_factory=list)
    """Script content as a list of lines (split by newline)."""

    read_only: bool = True
    """When True the editor is not editable by the user."""

    wrap_lines: bool = True
    """Whether long lines are wrapped in the editor view."""

    language: str | None = None
    """Language identifier (e.g., 'python') that supported by monaco-editor."""

    def get_control_type(self) -> str:
        return ScriptControl.__name__
