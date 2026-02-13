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
from cl.runtime.ui.control import Control
from cl.runtime.ui.control.core.selection import Selection


@dataclass(slots=True, kw_only=True, eq=False)
class PdfControl(Control):
    """Renders a PDF document inside the UI."""

    file: str | None = None
    """BLOB key pointing to the PDF file to display."""

    displayed_page: int | None = None
    """1-based page number to display; None defaults to the first page."""

    selections: list[Selection] | None = None
    """List of Selection objects to highlight parts of the page."""

    def get_control_type(self) -> str:
        return PdfControl.__name__
