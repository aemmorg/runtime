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
from cl.runtime.ui.control.card_content import CardContent
from cl.runtime.ui.control.control import Control


@dataclass(slots=True, kw_only=True, eq=False)
class CardControl(Control):
    """A UI card component that groups related content."""

    has_border: bool = False
    """Determines whether the card should display its border."""

    content: list[CardContent] = required(default_factory=list)
    """List of content elements to display within the card."""

    @classmethod
    def get_control_type(cls) -> str:
        return CardControl.__name__
