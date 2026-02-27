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
from cl.runtime.ui.control.control_key import ControlKey
from cl.runtime.ui.storage.control_loader import ControlLoader
from cl.runtime.ui.storage.control_saver import ControlSaver


@dataclass(slots=True, kw_only=True)
class ControlManager:
    """Manager of controls state."""

    root_node: Control | ControlKey = required()
    """Root node of the tree of Controls or key of root node."""

    def load(self) -> list[Control]:
        """Load a list of controls from the database by the given root node."""
        return ControlLoader(root_node=self.root_node.build()).load()

    def load_one(self) -> Control | None:
        """Load the root control from the database by the given root node."""
        return active(DataSource).load_one(self.root_node.build())

    def save(self):
        """Persist the control to the database."""
        ControlSaver(root_node=self.root_node.build()).save()

    def remove(self, *, selected_controls: list[str]):
        """Remove the given list of controls from the database."""
        ControlSaver(root_node=self.root_node.build()).remove_selected_controls(selected_controls=selected_controls)

    def reset(self, **kwargs):
        """
        Reset the control in root_node.
        kwargs: additional arguments passed to the control.
        """
        previous_controls = ControlLoader(root_node=self.root_node.get_key()).load()
        if previous_controls:
            active(DataSource).delete_many([control.get_key().build() for control in previous_controls], commit=True)
        control_type = type(self.root_node)
        new_root_node = control_type(
            control_path=self.root_node.control_path,
            view_for=self.root_node.view_for,
            view_name=self.root_node.view_name,
            **kwargs,
        )
        new_root_node.init()
        if hasattr(new_root_node, "init_content"):
            new_root_node.init_content()
        ControlSaver(root_node=new_root_node).save()
