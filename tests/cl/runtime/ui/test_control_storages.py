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
from dataclasses import dataclass
from typing import Any
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.ui.control.button_control import ButtonControl
from cl.runtime.ui.control.panel_control import PanelControl
from cl.runtime.ui.control.text_control import TextControl
from cl.runtime.ui.event.ui_event import UiEvent
from cl.runtime.ui.storage.control_loader import ControlLoader
from cl.runtime.ui.storage.control_manager import ControlManager
from cl.runtime.ui.storage.control_saver import ControlSaver
from stubs.cl.runtime.views.stub_viewers_key import StubViewersKey

_STUB_KEY = StubViewersKey(stub_id="A").build()
_STUB_KEY_2 = StubViewersKey(stub_id="Something").build()


def test_save_and_load_single_control(default_db_fixture):
    node = TextControl(view_for=_STUB_KEY, view_name="V", control_path="Root", value="Start")
    ControlManager(root_node=node.build()).save()

    # Reload and check change
    loaded = ControlManager(root_node=node.build()).load()
    assert len(loaded) == 1
    assert isinstance(loaded[0], TextControl)


def test_save_and_load_controls_tree(default_db_fixture, type_info_fixture):
    @dataclass(slots=True, kw_only=True, eq=False)
    class TestLoadTreeControlPanel(PanelControl):
        def init_content(self):
            text = TextControl(control_path="Text", value="Hello")
            self.attach_control(text)

            change_button = ButtonControl(
                control_path="ButtonChange",
            )
            self.attach_control(change_button)

        def on_change(self, key: str, field: str, value: Any, index: str | None = None) -> list[UiEvent]:
            events = []
            if key == "Root.ButtonChange" and field == "pressed":
                text = self.load_child("Text", TextControl)
                events += text.update_control(**{"value": "Changed", "wrap_lines": False})

            return events

    p = TestLoadTreeControlPanel(control_path="Root", view_for=_STUB_KEY_2, view_name="TestPanel")
    p.init_content()
    TypeInfo.register_type(TestLoadTreeControlPanel)

    ControlSaver(root_node=p.build()).save()
    loaded = ControlLoader(root_node=p.get_key().build()).load()

    assert len(loaded) == 3
    assert isinstance(loaded[0], TestLoadTreeControlPanel)
    assert isinstance(loaded[1], TextControl)
    assert isinstance(loaded[2], ButtonControl)


def test_load_by_path_without_parents(default_db_fixture, type_info_fixture):
    @dataclass(slots=True, kw_only=True, eq=False)
    class TestLoadControlPanel(PanelControl):
        def init_content(self):
            text = TextControl(control_path="Text", value="Hello")
            self.attach_control(text)

            change_button = ButtonControl(
                control_path="ButtonChange",
            )
            self.attach_control(change_button)

        def on_change(self, key: str, field: str, value: Any, index: str | None = None) -> list[UiEvent]:
            events = []
            if key == "Root.ButtonChange" and field == "pressed":
                text = self.load_child("Text", TextControl)
                events += text.update_control(**{"value": "Changed", "wrap_lines": False})

            return events

    p = TestLoadControlPanel(control_path="Root", view_for=_STUB_KEY_2, view_name="TestPanel")
    p.init_content()
    TypeInfo.register_type(TestLoadControlPanel)

    ControlSaver(root_node=p.build()).save()
    loaded = ControlLoader(root_node=p.get_key().clone()).load_by_path(control_path="Root.ButtonChange", parents=False)

    assert len(loaded) == 1
    assert isinstance(loaded[0], ButtonControl)


if __name__ == "__main__":
    pytest.main([__file__])
