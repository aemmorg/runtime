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
from cl.runtime.ui.event.partial_value_update_event import PartialValueUpdateEvent
from cl.runtime.ui.event.ui_event import UiEvent
from cl.runtime.ui.event.value_update_event import ValueUpdateEvent


@dataclass(slots=True, kw_only=True)
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

    def update_control(self, **kwargs) -> list[UiEvent]:
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
        return [
            ControlUpdateEvent(
                key=self.control_path,
                control=DataSerializers.FOR_UI.serialize(self, type_hint=field_spec.field_type_hint),
            )
        ]

    def update_value(self, field: str, value: Any) -> list[UiEvent]:
        """
        Update one control attribute value, and run onchange events.
        The result contains ValueUpdateEvent and events from on_change.

        Args:
            field: Name of the attribute to update in snake_case.
            value: New value for the attribute.
        """

        # Check if the attribute exists on the object
        if not hasattr(self, field):
            raise UserError("Such a key does not exist.")

        # Set field value
        setattr(self, field, value)

        # Persist new value, so it can be used in on_change method
        record = self.clone()
        active(DataSource).replace_one(record.build(), commit=True)

        data_type_spec = self.get_type_spec()
        field_spec = next((f for f in data_type_spec.fields if f.field_name == field), None)

        # Build a ValueUpdateEvent
        result = [
            ValueUpdateEvent(
                key=self.control_path,
                field=CaseUtil.snake_to_pascal_case(field),
                value=DataSerializers.FOR_UI.serialize(value, type_hint=field_spec.field_type_hint),
            ),
        ]

        # Notify the parent that the field has changed
        result += self.on_change(self.control_path, field, value)

        return result

    def update_partial_value(self, field: str, value: Any, index: str) -> list[UiEvent]:
        """
        Update partial one control attribute value.
        The result contains PartialValueUpdateEvent and events from on_change.

        Args:
            field: Name of the attribute to update in snake_case.
            value: New value for the attribute.
            index: Index of the element to update, supports nested paths separated by dots (e.g. "3.data.0").
        """

        # Check if the attribute exists on the object
        if not hasattr(self, field):
            raise UserError(f"Attribute '{field}' does not exist on control.")

        # Get the attribute value
        attr = getattr(self, field)
        if attr is None:
            raise UserError(f"Attribute '{field}' is None and cannot be partially updated.")

        # Split the index into parts for nested access
        index_parts = index.split(".")

        # Update the attribute value with nested index support
        attr = self._set_nested_value(attr, index_parts, value, field)

        # Set field value partial updated
        setattr(self, field, attr)

        # Persist new value, so it can be used in on_change method
        record = self.clone()
        active(DataSource).replace_one(record.build(), commit=True)

        data_type_spec = self.get_type_spec()
        field_spec = next((f for f in data_type_spec.fields if f.field_name == field), None)

        # Build a PartialValueUpdateEvent
        events = [
            PartialValueUpdateEvent(
                key=self.control_path,
                field=CaseUtil.snake_to_pascal_case(field),
                value=DataSerializers.FOR_UI.serialize(
                    value,
                    type_hint=self.get_partial_value_type_hint(field_spec.field_type_hint, index, attr),
                ),
                index=CaseUtil.snake_to_pascal_case(index) if CaseUtil.is_snake_case(index) else index,
            ),
        ]

        # Notify the parent that the field has changed
        events += self.on_change(self.control_path, field, value, index)

        return events

    @staticmethod
    def get_partial_value_type_hint(field_type_hint: TypeHint, index: str, attr: Any) -> TypeHint:
        """Get type hint for part of control field found by index."""

        type_hint = field_type_hint
        current = attr

        for part in index.split("."):
            if type_hint.remaining is not None:
                type_hint = type_hint.remaining
                if current is not None:
                    current = Control._get_nested_element(current, part, index)
            else:
                type_hint, current = Control._resolve_field_type_hint(type_hint, current, part, index)

        return type_hint

    @staticmethod
    def _resolve_field_type_hint(
        type_hint: TypeHint,
        current: Any,
        part: str,
        index: str,
    ) -> tuple[TypeHint, Any]:
        """Resolve a field type hint by looking up the field on the concrete runtime type."""

        concrete_type = type(current) if current is not None else type_hint.schema_type
        if not hasattr(concrete_type, "get_type_spec"):
            raise UserError(
                f"Cannot resolve field '{part}' on type '{concrete_type.__name__}' "
                f"in index path '{index}' (type does not have fields).",
            )
        data_spec = concrete_type.get_type_spec()
        field_spec = next((f for f in data_spec.fields if f.field_name == part), None)
        if field_spec is None:
            raise UserError(
                f"Field '{part}' does not exist on type '{concrete_type.__name__}'.",
            )
        next_current = getattr(current, part, None) if current is not None else None
        return field_spec.field_type_hint, next_current

    def update_layout(self) -> list[UiEvent]:
        """
        Update layout of the container and its children.
        The result contains LayoutUpdateEvent.
        """

        raise NotImplementedError("update_layout is not supported for this control.")

    @staticmethod
    def _get_nested_element(container: Any, index_part: str, field: str) -> Any:
        """Get an element from a container (Mapping or Sequence) by index part."""

        if isinstance(container, Mapping):
            if index_part not in container:
                raise UserError(f"Key '{index_part}' does not exist in mapping attribute '{field}'.")
            return container[index_part]
        elif isinstance(container, Sequence):
            try:
                int_index = int(index_part)
            except (ValueError, TypeError):
                raise UserError(
                    f"Index '{index_part}' cannot be converted to integer for sequence attribute '{field}'.",
                )
            if not (0 <= int_index < len(container)):
                raise UserError(
                    f"Index '{index_part}' is out of bounds for sequence attribute '{field}'.",
                )
            return container[int_index]
        elif hasattr(container, index_part):
            return getattr(container, index_part)
        else:
            raise UserError(
                f"Cannot traverse into '{index_part}' on attribute '{field}' "
                f"(must be a mapping, sequence, or object with attributes).",
            )

    @staticmethod
    def _set_element(container: Any, index_part: str, value: Any, field: str) -> Any:
        """Set an element in a container (Mapping, Sequence, or object) by index part, returning the updated container."""

        if isinstance(container, Mapping):
            container = dict(container)
            container[index_part] = value
            return container
        elif isinstance(container, Sequence):
            try:
                int_index = int(index_part)
            except (ValueError, TypeError):
                raise UserError(
                    f"Index '{index_part}' cannot be converted to integer for sequence attribute '{field}'.",
                )
            container = list(container)
            if not (0 <= int_index < len(container)):
                raise UserError(
                    f"Index '{index_part}' is out of bounds for sequence attribute '{field}'.",
                )
            container[int_index] = value
            return container
        elif hasattr(container, index_part):
            if hasattr(container, "clone"):
                container = container.clone()
            setattr(container, index_part, value)
            return container
        else:
            raise UserError(
                f"Cannot set value at '{index_part}' on attribute '{field}' "
                f"(must be a mutable mapping, sequence, or object with attributes).",
            )

    @staticmethod
    def _set_nested_value(attr: Any, index_parts: list[str], value: Any, field: str) -> Any:
        """
        Navigate into a nested structure using index parts and set the value at the deepest level.
        Returns the updated top-level attribute with mutable copies at each level.
        """

        # Collect (parent, index_part) pairs along the path to the deepest container
        path: list[tuple[Any, str]] = []
        current = attr

        if len(index_parts) > 1:
            for part in index_parts[:-1]:
                path.append((current, part))
                current = Control._get_nested_element(current, part, field)

        # Set value at the deepest level
        updated = Control._set_element(current, index_parts[-1], value, field)

        # Propagate updated values back up the path
        for container, part in reversed(path):
            updated = Control._set_element(container, part, updated, field)

        return updated

    def on_change(self, key: str, field: str, value: Any, index: str | None = None) -> list[UiEvent]:
        """
        Perform actions when a control attribute value changes.

        Args:
            key: Full path to the control that changed.
            field: Name of the attribute that changed in snake_case.
            value: New value of the attribute.
            index: Index of the element that changed (set for partial value updates).
        """

        if self._parent is not None:
            return self._parent.on_change(key, field, value, index=index)
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
