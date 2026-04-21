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
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.interactive_mixin import InteractiveMixin
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.ui.control import Control
from cl.runtime.ui.event.partial_value_update_event import PartialValueUpdateEvent
from cl.runtime.ui.event.ui_event import UiEvent
from cl.runtime.ui.event.ui_event_handler import UiEventHandler


@dataclass(slots=True, kw_only=True)
class PartialValueUpdateEventHandler(UiEventHandler[PartialValueUpdateEvent]):
    def process(self, target: Control | InteractiveMixin, event: PartialValueUpdateEvent) -> list[UiEvent]:
        """Process partial value update events."""
        snake_case_field = CaseUtil.pascal_to_snake_case(event.field)
        data_type_spec = target.get_type_spec()
        field_spec = next((field for field in data_type_spec.fields if field.field_name == snake_case_field), None)
        if field_spec is None:
            raise RuntimeError(f"Target with key={target.get_key()} does not have key={snake_case_field}")

        attr = getattr(target, snake_case_field)
        value = DataSerializers.FOR_UI.deserialize(
            event.value, type_hint=target.get_partial_value_type_hint(field_spec.field_type_hint, event.index, attr)
        )
        if hasattr(value, "build"):
            value = value.build()

        return target.update_partial_value(snake_case_field, value, event.index)
