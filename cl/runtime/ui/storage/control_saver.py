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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.ui.control import Control


@dataclass(slots=True, kw_only=True)
class ControlSaver:
    """
    Saves the state of custom UI, that is represented by a tree of Control objects to a persistent storage.
    """

    root_node: Control = required()
    """Root  node of the tree of Controls"""

    def save(self):
        """Save the tree of custom UI Controls starting at root_node"""
        self._perform_bfs(self.root_node, self._save_node)

    def remove_selected_controls(self, *, selected_controls: list[str]):
        """
        Remove selected (by list of control paths) controls from the tree of custom UI Controls,
        and their children.
        """

        def _find_selected_node(node: Control):
            if node.control_path in selected_controls:
                self._perform_bfs(node, lambda n: active(DataSource).delete_one(n.get_key().build(), commit=True))

        self._perform_bfs(self.root_node, _find_selected_node)

    @staticmethod
    def _save_node(node: Control):
        active(DataSource).replace_one(node.build(), commit=True)

    @staticmethod
    def _perform_bfs(root_node: Control, callback):
        """Perform breadth-first search of the tree of Controls starting at root_node"""
        node_stack = [root_node]
        while len(node_stack) > 0:
            node = node_stack.pop()
            callback(node)
            for child in node.get_children():
                node_stack.append(child)
