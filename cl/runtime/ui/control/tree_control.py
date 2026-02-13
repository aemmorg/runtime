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
from typing import Final
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.ui.control import Control
from cl.runtime.ui.control.tree_control_node import TreeControlNode

SEPARATOR: Final[str] = "."


@dataclass(slots=True, kw_only=True, eq=False)
class TreeControl(Control):
    """Control representing a tree of nodes with text."""

    selected_node_path: str = required()
    """The id of the selected node."""

    # TODO: Consider to make dict of dicts
    child_nodes: list[TreeControlNode] = required(default_factory=list)
    """List of top level tree nodes."""

    expanded_nodes: list[str] = required(default_factory=list)
    """List of values of the expanded nodes, e.g. ["node_1", "node_1/node_2"]."""

    @classmethod
    def separator(cls) -> str:
        return SEPARATOR

    def init(self):
        self._add_selected_node_to_expanded_nodes()

    def _get_path_parts(self, path: str) -> list[str]:
        """Split path to tokens. "a.b.c" -> ["a", "a.b", "a.b.c"]"""
        path = path.strip()
        if path == ".":
            return ["."]

        parts = path.split(self.separator())
        result = []
        current = []

        for part in parts:
            current.append(part)
            result.append(".".join(current))
        return result

    def _add_selected_node_to_expanded_nodes(self):
        """Convert tokens to path. "a.b.c" -> ["a", "a.b", "a.d.c"]"""
        if self.selected_node_path is None:
            return
        path_parts = self._get_path_parts(self.selected_node_path)
        for part in path_parts:
            if part not in self.expanded_nodes:
                self.expanded_nodes.append(part)

    def get_control_type(self) -> str:
        return TreeControl.__name__
