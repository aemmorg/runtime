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

import pytest
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.ui.control.text_control import TextControl
from cl.runtime.ui.event.control_update_event import ControlUpdateEvent
from cl.runtime.ui.event.layout_update_event import LayoutUpdateEvent
from cl.runtime.ui.event.partial_value_update_event import PartialValueUpdateEvent
from cl.runtime.ui.event.runtime_error_event import RuntimeErrorEvent
from cl.runtime.ui.event.user_error_event import UserErrorEvent
from cl.runtime.ui.event.value_update_event import ValueUpdateEvent
from stubs.cl.runtime.views.stub_viewers_key import StubViewersKey

_STUB_KEY = StubViewersKey(stub_id="A").build()
_UI_SERIALIZER = BootstrapSerializers.FOR_UI_EVENTS
SUPPORTED_EVENTS = [
    ValueUpdateEvent(key="Root", field="Value", value="Value"),
    PartialValueUpdateEvent(key="Root", field="Value", value="Value", index="1"),
    ControlUpdateEvent(
        key="Root", control=TextControl(view_for=_STUB_KEY, view_name="V", control_path="Root", value="Start")
    ),
    LayoutUpdateEvent(
        key="Root",
        added_controls=[TextControl(view_for=_STUB_KEY, view_name="V", control_path="Root", value="Start")],
        removed_controls=["root.test"],
    ),
    RuntimeErrorEvent(key="Root", error="Test error"),
    UserErrorEvent(key="Root", error="Test error"),
]

ExpectedResults = [
    {
        "Key": "Root",
        "Field": "Value",
        "Value": "Value",
        "_t": "ValueUpdateEvent",
    },
    {
        "Key": "Root",
        "Field": "Value",
        "Value": "Value",
        "Index": "1",
        "_t": "PartialValueUpdateEvent",
    },
    {
        "Key": "Root",
        "Control": {
            "ControlPath": "Root",
            "ViewFor": _STUB_KEY,
            "ViewName": "V",
            "Hidden": False,
            "Label": None,
            "ParentKey": None,
            "Style": None,
            "Enabled": True,
            "Collapsible": False,
            "Value": "Start",
            "WrapLines": True,
            "ControlType": "TextControl",
            "_t": "TextControl",
        },
        "_t": "ControlUpdateEvent",
    },
    {
        "Key": "Root",
        "AddedControls": (
            {
                "ControlPath": "Root",
                "ViewFor": _STUB_KEY,
                "ViewName": "V",
                "Hidden": False,
                "Label": None,
                "ParentKey": None,
                "Style": None,
                "Enabled": True,
                "Collapsible": False,
                "Value": "Start",
                "WrapLines": True,
                "ControlType": "TextControl",
                "_t": "TextControl",
            },
        ),
        "RemovedControls": ("root.test",),
        "_t": "LayoutUpdateEvent",
    },
    {
        "Key": "Root",
        "Error": "Test error",
        "_t": "RuntimeErrorEvent",
    },
    {
        "Key": "Root",
        "Error": "Test error",
        "_t": "UserErrorEvent",
    },
]


if __name__ == "__main__":
    pytest.main([__file__])
