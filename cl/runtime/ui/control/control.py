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

from abc import ABC
from abc import abstractmethod
from collections.abc import Mapping
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import TypeVar
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.ui.control.control_key import ControlKey
from cl.runtime.ui.event.control_event import ControlEvent
from cl.runtime.ui.event.partial_value_update_event import PartialValueUpdateEvent
from cl.runtime.ui.event.value_update_event import ValueUpdateEvent


@dataclass(slots=True, kw_only=True, eq=False)
class Control(ControlKey, RecordMixin, ABC):
    """
    Base class for all UI controls.
    Controls are serializable records identified by control_path.

    Update Methods:
        - update_control(**kwargs): Update multiple attributes atomically, returns ControlUpdateEvent
        - update_value(key, value): Update a single attribute, returns ValueUpdateEvent + on_change events
        - update_partial_value(key, value, index): Update an element within a mutable mapping or sequence,
          returns PartialValueUpdateEvent + on_change events

    All update methods persist changes to storage and trigger the on_change event propagation chain.
    """

    parent_key: ControlKey | None = None
    """Reference to a parent Control record stored in persistence."""

    label: str | None = None
    """Optional label shown alongside the control in the UI."""

    style: str | None = None
    """Styling hints applied by the renderer (CSS classes, etc.)."""

    hidden: bool = False
    """When True the control should not be visible to the user."""

    enabled: bool = True
    """When False the control is visually disabled and not interactive."""

    collapsible: bool | None = False
    """If True the control can be collapsed/expanded by the UI."""

    _parent: Optional["Control"] = None
    """Runtime reference to the parent Control instance for event propagation."""

    @classmethod
    def get_key_type(cls) -> type[KeyMixin]:
        return ControlKey

    def get_key(self) -> ControlKey:
        return ControlKey(view_name=self.view_name, view_for=self.view_for, control_path=self.control_path).build()

    def update_control(self, **kwargs) -> list[ControlEvent]:
        """
        Update many control attribute values.
        The result contains ControlUpdateEvent.

        Args:
            **kwargs: Keyword arguments with attribute names in snake_case and new values.
        """

        from cl.runtime.ui.event.control_update_event import ControlUpdateEvent

        # Update attributes
        for attribute, value in kwargs.items():
            setattr(self, attribute, value)

        # Persist new value, so it can be used in on_change
        record = self.clone()
        active(DataSource).replace_one(record.build(), commit=True)

        data_type_spec = ControlUpdateEvent.get_type_spec()
        field_spec = next((field for field in data_type_spec.fields if field.field_name == "control"), None)

        # Build a ControlUpdateEvent
        return [ControlUpdateEvent(
            control_path=self.control_path,
            control=DataSerializers.FOR_UI.serialize(self, type_hint=field_spec.field_type_hint),
        )]

    def update_value(self, key: str, value: Any) -> list[ControlEvent]:
        """
        Update one control attribute value, and run onchange events.
        The result contains ValueUpdateEvent and events from on_change.

        Args:
            key: Name of the attribute to update in snake_case.
            value: New value for the attribute.
        """

        # Check if the attribute exists on the object
        if not hasattr(self, key):
            raise UserError("Such a key does not exist.")

        # Set field value
        setattr(self, key, value)

        # Persist new value, so it can be used in on_change method
        record = self.clone()
        active(DataSource).replace_one(record.build(), commit=True)

        data_type_spec = self.get_type_spec()
        field_spec = next((field for field in data_type_spec.fields if field.field_name == key), None)

        # Build a ValueUpdateEvent
        result = [
            ValueUpdateEvent(
                control_path=self.control_path,
                key=CaseUtil.snake_to_pascal_case(key),
                value=DataSerializers.FOR_UI.serialize(value, type_hint=field_spec.field_type_hint),
            ),
        ]

        # Notify the parent that the field has changed
        result += self.on_change(self.control_path, key, value)

        return result

    def update_partial_value(self, key: str, value: Any, index: str) -> list[ControlEvent]:
        """
        Update partial one control attribute value.
        The result contains PartialValueUpdateEvent and events from on_change.

        Args:
            key: Name of the attribute to update in snake_case.
            value: New value for the attribute.
            index: Index of the element to update.
        """

        # Check if the attribute exists on the object
        if not hasattr(self, key):
            raise UserError(f"Attribute '{key}' does not exist on control.")

        # Get the attribute value
        attr = getattr(self, key)
        if attr is None:
            raise UserError(f"Attribute '{key}' is None and cannot be partially updated.")

        # Update the attribute value based on its type
        # Only mutable maps and mutable ordered sequences are supported
        if isinstance(attr, Mapping):
            attr = dict(attr)

            attr[index] = value
        elif isinstance(attr, Sequence):
            try:
                int_index = int(index)
            except (ValueError, TypeError):
                raise UserError(
                    f"Index '{index}' cannot be converted to integer for sequence attribute '{key}'.",
                )

            attr = list(attr)

            if not (0 <= int_index < len(attr)):
                raise UserError(
                    f"Index '{index}' is out of bounds for sequence attribute '{key}'.",
                )
            attr[int_index] = value
        else:
            raise UserError(
                f"Attribute '{key}' does not support indexed assignment (must be a mutable mapping or sequence).",
            )

        # Set field value partial updated
        setattr(self, key, attr)

        # Persist new value, so it can be used in on_change method
        record = self.clone()
        active(DataSource).replace_one(record.build(), commit=True)

        data_type_spec = self.get_type_spec()
        field_spec = next((field for field in data_type_spec.fields if field.field_name == key), None)

        # Build a PartialValueUpdateEvent
        events = [
            PartialValueUpdateEvent(
                control_path=self.control_path,
                key=CaseUtil.snake_to_pascal_case(key),
                value=DataSerializers.FOR_UI.serialize(
                    value,
                    type_hint=self.get_partial_value_type_hint(field_spec.field_type_hint, index),
                ),
                index=index,
            ),
        ]

        # Notify the parent that the field has changed
        events += self.on_change(self.control_path, key, attr)

        return events

    @staticmethod
    def get_partial_value_type_hint(field_type_hint: TypeHint, index: str) -> TypeHint:
        """Get type hint for part of control field found by index."""

        type_hint = field_type_hint

        for _ in index.split("."):
            type_hint = type_hint.remaining

        return type_hint

    def update_layout(self) -> list[ControlEvent]:
        """
        Update layout of the container and its children.
        The result contains LayoutUpdateEvent.
        """

        raise NotImplementedError("update_layout is not supported for this control.")

    def on_change(self, control_path: str, key: str, value: str) -> list[ControlEvent]:
        """
        Perform actions when a control attribute value changes.

        Args:
            control_path: Full path to the control that changed.
            key: Name of the attribute that changed in snake_case.
            value: New value of the attribute.
        """

        if self._parent is not None:
            return self._parent.on_change(control_path, key, value)
        return []

    @abstractmethod
    def get_control_type(self) -> str:
        """String representation of control type for serialization."""

        raise NotImplementedError("get_control_type must be implemented by subclasses.")

    def get_children(self) -> list["Control"]:
        """Return child controls if available."""

        return []

    def set_parent(self, parent: "Control") -> None:
        """Update parent control."""

        self._parent = parent


TControl = TypeVar("TControl", bound=Control)
