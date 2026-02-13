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


@dataclass(slots=True, kw_only=True)
class CardListContent(CardContent):
    """
    A card content variant that holds an ordered list of bullet items.
    Each item is rendered as a separate list entry; strings should be pre-escaped or plain text.
    """

    items: list[str] = required(default_factory=list)
    """Ordered list of item strings to display as bullets."""
