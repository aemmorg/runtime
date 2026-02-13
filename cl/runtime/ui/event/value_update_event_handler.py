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
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.ui.control import Control
from cl.runtime.ui.event.control_event_handler import ControlEventHandler
from cl.runtime.ui.event.value_update_event import ValueUpdateEvent


@dataclass(slots=True, kw_only=True)
class ValueUpdateEventHandler(ControlEventHandler[ValueUpdateEvent]):
    def process(self, control: Control, event: ValueUpdateEvent):
        """Process control events."""
        snake_case_key = CaseUtil.pascal_to_snake_case(event.key)
        data_type_spec = control.get_type_spec()
        field_spec = next((field for field in data_type_spec.fields if field.field_name == snake_case_key), None)
        if field_spec is None:
            raise RuntimeError(f"Control with key={control.get_key()} does not have key={snake_case_key}")

        value = DataSerializers.FOR_UI.deserialize(event.value, type_hint=field_spec.field_type_hint)

        return control.update_value(snake_case_key, value)
