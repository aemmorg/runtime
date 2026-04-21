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
from cl.runtime.records.variant.text_container import TextContainer


@dataclass(slots=True, kw_only=True)
class TreeContainer(TextContainer):
    """Column data container with tree-structured row labels.

    Each entry in 'data' is a dot-separated path expressing parent-child
    relationships. Parent nodes must appear before their children.

    Example (node_separator="."):
        ["Revenue", "Revenue.Product", "Revenue.Services", "Expenses"]
    """

    node_separator: str = required()
    """Character used to separate hierarchy levels in row label paths (typically ".")."""
