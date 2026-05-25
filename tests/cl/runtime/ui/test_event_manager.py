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
from cl.runtime.ui.control.text_control import TextControl
from cl.runtime.ui.event.event_manager import EventManager
from cl.runtime.ui.event.runtime_error_event import RuntimeErrorEvent
from cl.runtime.ui.event.value_update_event import ValueUpdateEvent
from cl.runtime.ui.resolver.control_target_resolver import ControlTargetResolver
from cl.runtime.ui.storage.control_manager import ControlManager
from stubs.cl.runtime.views.stub_viewers_key import StubViewersKey

_STUB_KEY = StubViewersKey(stub_id="A").build()


def test_dispatch_event_success(default_db_fixture):
    node = TextControl(view_for=_STUB_KEY, view_name="V", control_path="root", value="Start")
    ControlManager(root_node=node.build()).save()
    em = EventManager(resolver=ControlTargetResolver(key="A", type_name="StubViewers", viewer_name="V"))
    event = {"Key": "root", "Field": "Value", "Value": "Changed", "_t": "ValueUpdateEvent"}
    out_events = em.dispatch(event)
    assert isinstance(out_events[0], ValueUpdateEvent)
    assert out_events[0].key == "root"
    assert out_events[0].field == "Value"
    assert out_events[0].value == "Changed"

    # Reload and check change
    loaded = ControlManager(root_node=node.build()).load()
    assert loaded[0].value == "Changed"


def test_not_supported_event(default_db_fixture):
    node = TextControl(view_for=_STUB_KEY, view_name="V", control_path="root", value="Start")
    ControlManager(root_node=node.build()).save()
    em = EventManager(resolver=ControlTargetResolver(key="A", type_name="StubViewers", viewer_name="V"))
    event = {
        "Key": "root",
        "Control": {"ControlPath": "Root", "ViewFor": "A", "ViewName": "V", "Value": "Changed", "_t": "TextControl"},
        "_t": "ControlUpdateEvent",
    }
    out_events = em.dispatch(event)
    assert isinstance(out_events[0], RuntimeErrorEvent)
    assert out_events[0].key == "root"
    assert out_events[0].error == "Unknown event ControlUpdateEvent"


def test_event_without_t(default_db_fixture):
    node = TextControl(view_for=_STUB_KEY, view_name="V", control_path="root", value="Start")
    ControlManager(root_node=node.build()).save()
    em = EventManager(resolver=ControlTargetResolver(key="A", type_name="StubViewers", viewer_name="V"))
    event_without_t = {
        "Key": "A",
        "Control": {"ControlPath": "Root", "ViewFor": "A", "ViewName": "V", "Value": "Changed", "_t": "TextControl"},
    }
    out_events_without_t = em.dispatch(event_without_t)

    assert out_events_without_t == []


if __name__ == "__main__":
    pytest.main([__file__])
