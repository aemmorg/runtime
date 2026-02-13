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
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class HighlightedArea(DataclassMixin):
    """Highlighted area in the pdf file."""

    x: float = required()
    """X coordinate of the top left corner of the area"""

    y: float = required()
    """Y coordinate of the top left corner of the area"""

    width: float = required()
    """Width of the area"""

    height: float = required()
    """Height of the area"""

    page: int = required()
    """Number of the page on which highlighted area is located."""
