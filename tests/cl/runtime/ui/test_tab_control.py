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
from typing import Any
import pytest
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.ui.control.button_control import ButtonControl
from cl.runtime.ui.control.label_control import LabelControl
from cl.runtime.ui.control.panel_control import PanelControl
from cl.runtime.ui.control.tab_control import TabControl
from cl.runtime.ui.control.text_control import TextControl
from cl.runtime.ui.event.event_manager import EventManager
from cl.runtime.ui.event.layout_update_event import LayoutUpdateEvent
from cl.runtime.ui.event.ui_event import UiEvent
from cl.runtime.ui.event.value_update_event import ValueUpdateEvent
from cl.runtime.ui.resolver.control_target_resolver import ControlTargetResolver
from cl.runtime.ui.storage.control_loader import ControlLoader
from cl.runtime.ui.storage.control_saver import ControlSaver
from stubs.cl.runtime.views.stub_viewers_key import StubViewersKey

_STUB_KEY = StubViewersKey(stub_id="TabTest").build()


def test_create_new_tab_initial(default_db_fixture, type_info_fixture):
    """Test that create_new_tab returns ValueUpdateEvent during initial creation."""

    @dataclass(slots=True, kw_only=True, eq=False)
    class TestTabInitialPanel(PanelControl):
        def init_content(self):
            tab_ctrl = TabControl(control_path="tabs")
            self.attach_control(tab_ctrl)

            tab1 = PanelControl(control_path="panel1")
            events1 = tab_ctrl.create_new_tab("First", tab1)
            assert len(events1) == 1
            assert isinstance(events1[0], ValueUpdateEvent)
            assert events1[0].field == "TabHeaders"

            tab2 = PanelControl(control_path="panel2")
            events2 = tab_ctrl.create_new_tab("Second", tab2)
            assert len(events2) == 1
            assert list(events2[0].value) == ["First", "Second"]

    p = TestTabInitialPanel(control_path="root", view_for=_STUB_KEY, view_name="TestPanel")
    p.init_content()
    TypeInfo.register_type(TestTabInitialPanel)

    ControlSaver(root_node=p.build()).save()
    loaded = ControlLoader(root_node=p.get_key().build()).load()

    # Root panel + TabControl + 2 tab panels
    assert len(loaded) == 4

    tab_ctrl = loaded[1]
    assert isinstance(tab_ctrl, TabControl)
    assert list(tab_ctrl.tab_headers) == ["First", "Second"]
    assert tab_ctrl.control_path == "root.tabs"


def test_create_new_tab_dynamic(default_db_fixture, type_info_fixture):
    """Test that create_new_tab returns ValueUpdateEvent when adding to existing TabControl."""

    @dataclass(slots=True, kw_only=True, eq=False)
    class TestTabDynamicPanel(PanelControl):
        def init_content(self):
            tab_ctrl = TabControl(control_path="tabs")
            self.attach_control(tab_ctrl)

            tab1 = PanelControl(control_path="panel1")
            tab_ctrl.create_new_tab("First", tab1)

            text = TextControl(control_path="text", value="Hello")
            tab1.attach_control(text)

            add_btn = ButtonControl(control_path="add_btn")
            self.attach_control(add_btn)

        def on_change(self, key: str, field: str, value: Any, index: str | None = None) -> list[UiEvent]:
            events = []
            if key.endswith("add_btn") and field == "pressed":
                tab_ctrl = self.load_child("tabs", TabControl)
                new_panel = PanelControl(control_path="new_panel")
                events += tab_ctrl.create_new_tab("Dynamic Tab", new_panel)

                label = LabelControl(control_path="label", value="Added dynamically")
                new_panel.attach_control(label)

                events += tab_ctrl.update_layout()
            return events

    p = TestTabDynamicPanel(control_path="root", view_for=_STUB_KEY, view_name="TestPanel")
    p.init_content()
    TypeInfo.register_type(TestTabDynamicPanel)

    ControlSaver(root_node=p.build()).save()

    # Simulate button press to add a new tab
    em = EventManager(resolver=ControlTargetResolver(key=_STUB_KEY, viewer_name="TestPanel"))
    events = em.dispatch(
        {
            "_t": "ValueUpdateEvent",
            "Key": "root.add_btn",
            "Field": "Pressed",
            "Value": True,
        },
    )

    # Expect: ValueUpdateEvent for pressed + ValueUpdateEvent for tab_headers + LayoutUpdateEvent
    value_events = [e for e in events if isinstance(e, ValueUpdateEvent)]
    layout_events = [e for e in events if isinstance(e, LayoutUpdateEvent)]

    # tab_headers update event
    tab_header_events = [e for e in value_events if e.key == "root.tabs" and e.field == "TabHeaders"]
    assert len(tab_header_events) == 1
    assert list(tab_header_events[0].value) == ["First", "Dynamic Tab"]

    # Layout update event
    assert len(layout_events) == 1

    # Verify persisted state
    reloaded = ControlLoader(root_node=p.get_key().build()).load()
    tab_ctrls = [c for c in reloaded if isinstance(c, TabControl)]
    assert len(tab_ctrls) == 1
    assert list(tab_ctrls[0].tab_headers) == ["First", "Dynamic Tab"]


if __name__ == "__main__":
    pytest.main([__file__])
