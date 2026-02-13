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

import contextlib
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.for_dataclasses.extensions import optional
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.ui.control import Control
from cl.runtime.ui.control.control import TControl
from cl.runtime.ui.control.control_key import ControlKey
from cl.runtime.ui.control.exceptions.control_exceptions import ChildNotFoundError
from cl.runtime.ui.event.control_event import ControlEvent
from cl.runtime.ui.storage.control_manager import ControlManager


@dataclass(slots=True, kw_only=True, eq=False)
class ControlContainer(Control, ABC):
    """Base class for controls that contains child controls."""

    control_keys: list[ControlKey] = required(default_factory=list)
    """List of child control keys persisted in storage."""

    _controls: list[Control] | None = optional(default_factory=list)
    """In-memory list of child Control instances (not persisted)."""

    _added_controls: list[Control] | None = optional(default_factory=list)
    """List of controls that were added to container."""

    _removed_controls: list[str] | None = optional(default_factory=list)
    """List of control paths of controls that were removed from container."""

    def get_children(self) -> list[Control]:
        """Return child controls if available."""

        return self._controls or []

    def update_layout(self) -> list[ControlEvent]:
        """
        Update layout of the container and its children.
        The result contains LayoutUpdateEvent.
        """

        from cl.runtime.ui.event.layout_update_event import LayoutUpdateEvent

        # Rebuild the layout
        self._save_changes_in_db()

        data_type_spec = LayoutUpdateEvent.get_type_spec()
        field_spec = next((field for field in data_type_spec.fields if field.field_name == "added_controls"), None)

        # Build a LayoutUpdateEvent
        return [
            LayoutUpdateEvent(
                control_path=self.control_path,
                removed_controls=self._removed_controls,
                added_controls=DataSerializers.FOR_UI.serialize(
                    self.list_added_controls(self),
                    type_hint=field_spec.field_type_hint
                ),
            ),
        ]

    @staticmethod
    def list_added_controls(root_control: Control) -> list[Control]:
        """Collect all nested added controls into a flat structure."""

        result = []

        def walk(obj):
            for item in getattr(obj, "_added_controls", []) or []:
                result.append(item)
                walk(item)

        walk(root_control)
        return result

    def attach_control(self, control: Control) -> None:
        """Attach child control to parent ControlContainer."""
        # To be able to modify a sequence loaded from the database.
        self._controls = list(self._controls)
        self.control_keys = list(self.control_keys)
        self._added_controls = list(self._added_controls)

        self._controls.append(control)
        control.parent_key = self.get_key()
        control.control_path = f"{self.control_path}.{control.control_path}"
        control.view_for = self.view_for
        control.view_name = self.view_name
        self.control_keys.append(control.get_key())
        self._added_controls.append(control)

    def load_child(self, control_path: str, cast_to: type[TControl] = Control) -> TControl:
        """
        Load child control with control_path from storage.

        Args:
            control_path: Path to a child control at any depth, relative to self.control_path.
                Can be a dot-separated path like "child1.child2".
            cast_to: Type to cast the loaded control to.
        """

        full_control_path = f"{self.control_path}.{control_path}"
        child_key = ControlKey(
            view_for=self.view_for,
            view_name=self.view_name,
            control_path=full_control_path,
        )
        control = active(DataSource).load_one_or_none(child_key.build())
        if control is None:
            raise ChildNotFoundError(f"Control with path '{full_control_path}' not found.")
        return control.clone()

    def remove_control(self, control_path: str) -> None:
        """
        Remove control with its children from the container.
        This method only marks the control as removed. To save changes, call update_layout.

        Args:
            control_path: Path to a child control at any depth, relative to self.control_path.
                Can be a dot-separated path like "child1.child2".
        """
        # To be able to modify a sequence loaded from the database.
        self._removed_controls = list(self._removed_controls)

        controls_to_remove: list[str] = []

        # Recursively find all controls to remove and collect their paths
        def find_controls(control: Control):
            controls_to_remove.append(control.control_path)
            if not isinstance(control, ControlContainer):
                return
            for child_key in control.control_keys:
                find_controls(control.load_child(child_key.control_path.split(".")[-1]))

        find_controls(self.load_child(control_path))

        # Mark controls as removed
        for child_control in controls_to_remove:
            self._removed_controls.append(child_control)

    @abstractmethod
    def init_content(self):
        """Method for filling the container with child controls."""

    def _append_saved_children(self):
        """
        Check if self._controls contains all controls from self.control_keys,
        and append missing controls to self._controls.
        """

        new_controls = []
        loaded_control_paths: list[str] = [control.control_path for control in self._controls]

        # Load missing controls
        for control_key in self.control_keys:
            control_path = control_key.control_path.removeprefix(f"{self.control_path}.")
            # Skip control that is already loaded
            if control_path in loaded_control_paths:
                continue
            # Otherwise load it
            with contextlib.suppress(ChildNotFoundError):
                new_controls.append(self.load_child(control_path))

        self._controls.extend(new_controls)

    def _save_changes_in_db(self):
        """Save layout container changes into database."""

        # Load missing controls to self._controls
        self._append_saved_children()

        # Remove controls that were marked as removed
        node = self.clone()
        ControlManager(root_node=node).remove(selected_controls=self._removed_controls)

        # Check if control was added or updated, skip unchanged controls
        used_paths = set()
        added_control_paths = frozenset([control.control_path for control in self._added_controls])
        removed_control_paths = frozenset(self._removed_controls)

        def is_control_added_or_updated(control: Control) -> bool:
            is_not_duplicate = control.control_path not in used_paths
            is_added = control.control_path in added_control_paths
            is_removed = control.control_path in removed_control_paths
            is_updated = is_added and is_removed
            return is_not_duplicate and (not is_removed or is_updated)

        # Collect controls that were added or updated
        new_child_controls = []
        for control in self._controls:
            if is_control_added_or_updated(control):
                used_paths.add(control.control_path)
                new_child_controls.append(control)

        # Update control keys and loaded controls
        self.control_keys = [control.get_key() for control in new_child_controls]
        self._controls = new_child_controls
        ControlManager(root_node=self).save()
