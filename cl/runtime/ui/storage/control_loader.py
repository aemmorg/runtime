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

from __future__ import annotations
from dataclasses import dataclass
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.ui.control import Control
from cl.runtime.ui.control.control_key import ControlKey


@dataclass(slots=True, kw_only=True)
class ControlLoader:
    """
    Loads a tree of Controls starting from a root ControlKey.
    Can also load a single control together with its parent chain
    (used for event handling).
    """

    root_node: ControlKey = required()
    """Root ControlKey of the control tree"""

    _result: list[Control] = required(default_factory=list)
    """Flat list of loaded controls"""

    def load(self) -> list[Control]:
        """
        Load the full control tree starting from the root node.
        """
        self._load_node(self.root_node)
        return self._result

    def load_by_path(
        self,
        control_path: str,
        parents: bool = True,
    ) -> list[Control]:
        """
        Load a control by its path and (optionally) all its parents.
        This is typically used when handling UI events.
        """

        controls: list[Control] = []

        # Start from the root and override the path we want to resolve
        control_key = self.root_node
        control_key.control_path = control_path

        # Walk up the parent chain
        while control_key:
            control = self._load_single_control(control_key)
            controls.append(control)

            if not parents:
                break

            control_key = control.parent_key

        # Link parent/child relationships and finalize construction
        for child, parent in zip(controls, controls[1:]):
            child.set_parent(parent)

        return controls

    def _load_node(self, node_key: ControlKey) -> None:
        """
        Recursively load a control and all its children.
        """

        node = active(DataSource).load_one_or_none(node_key.build())

        if node is None:
            return

        self._result.append(node)

        # Recursively load children if they exist
        for child_key in getattr(node, "control_keys", []) or []:
            self._load_node(child_key)

    def _load_single_control(self, control_key: ControlKey) -> Control:
        """
        Load a single control.
        Falls back to resolving data-container controls if needed.
        """

        control = active(DataSource).load_one_or_none(control_key.build())

        if control:
            return control.clone()

        control = self._check_for_data_container(control_key)
        if control:
            return control.clone()

        raise RuntimeError(f"Control({control_key}) not found")

    @staticmethod
    def _check_for_data_container(control_key: ControlKey) -> Control | None:
        """
        Try to resolve a control that represents a data container item.

        Example:
            control.path = "list.3"
            → load "list" and assign event index = 3
        """

        parts = control_key.control_path.split(".")
        if len(parts) < 2:
            return None

        index_part = parts[-1]
        if not index_part.isdigit():
            return None

        # Load the parent container control
        control_key.control_path = ".".join(parts[:-1])
        control = active(DataSource).load_one(control_key.build())

        return control
