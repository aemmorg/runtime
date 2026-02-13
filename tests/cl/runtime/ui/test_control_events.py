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
from cl.runtime.records.variant import StrVariant
from cl.runtime.records.variant import Variant
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.ui.control.button_control import ButtonControl
from cl.runtime.ui.control.panel_control import PanelControl
from cl.runtime.ui.control.table_control import TableControl
from cl.runtime.ui.control.text_control import TextControl
from cl.runtime.ui.event.control_event import ControlEvent
from cl.runtime.ui.event.control_update_event import ControlUpdateEvent
from cl.runtime.ui.event.event_manager import EventManager
from cl.runtime.ui.event.partial_value_update_event import PartialValueUpdateEvent
from cl.runtime.ui.storage.control_loader import ControlLoader
from cl.runtime.ui.storage.control_saver import ControlSaver


def test_partial_value_update_event(default_db_fixture):
    @dataclass(slots=True, kw_only=True, eq=False)
    class TestPartialValuePanel(PanelControl):
        def init_content(self):
            table = TableControl(
                control_path="Table",
                col_names=["index", "string_element", "double_element"],
                data=[Variant.create("Val1"), Variant.create("Val2"), Variant.create("Val3")],
            )
            table.init()
            self.attach_control(table)

            change_button = ButtonControl(
                control_path="ButtonChange",
            )
            self.attach_control(change_button)

        def on_change(self, control_path: str, key: str, value: Any) -> list[ControlEvent]:
            events = []
            if control_path == "Root.ButtonChange" and key == "pressed":
                table = self.load_child("Table", TableControl)
                events += table.update_partial_value("data", Variant.create("Changed"), "1")

            return events

    p = TestPartialValuePanel(control_path="Root", view_for="Something", view_name="TestPanel")
    p.init_content()
    TypeInfo._add_type(TestPartialValuePanel)

    ControlSaver(root_node=p.build()).save()
    loaded = ControlLoader(root_node=p.get_key().build()).load()

    assert loaded[1].control_path == "Root.Table"
    assert loaded[1].data == (
        StrVariant(metadata=None, value="Val1"),
        StrVariant(metadata=None, value="Val2"),
        StrVariant(metadata=None, value="Val3"),
    )

    em = EventManager(root_node=p)
    events = em.dispatch(
        {
            "_t": "ValueUpdateEvent",
            "ControlPath": "Root.ButtonChange",
            "Key": "Pressed",
            "Value": True,
        },
    )
    assert len(events) == 2
    assert isinstance(events[1], PartialValueUpdateEvent)
    assert events[1].control_path == "Root.Table"
    assert events[1].key == "Data"
    assert events[1].value == {"_t": "StrVariant", "Metadata": None, "Value": "Changed"}
    assert events[1].index == "1"


def test_value_update_event(default_db_fixture):
    @dataclass(slots=True, kw_only=True, eq=False)
    class TestValuePanel(PanelControl):
        def init_content(self):
            text = TextControl(control_path="Text", value="Hello")
            self.attach_control(text)

            change_button = ButtonControl(
                control_path="ButtonChange",
            )
            self.attach_control(change_button)

        def on_change(self, control_path: str, key: str, value: Any) -> list[ControlEvent]:
            events = []
            if control_path == "Root.ButtonChange" and key == "pressed":
                text = self.load_child("Text", TextControl)
                events += text.update_value("value", "Changed")

            return events

    p = TestValuePanel(control_path="Root", view_for="Something", view_name="TestPanel")
    p.init_content()
    TypeInfo._add_type(TestValuePanel)

    ControlSaver(root_node=p.build()).save()
    loaded = ControlLoader(root_node=p.get_key().build()).load()

    assert loaded[1].control_path == "Root.Text"
    assert loaded[1].value == "Hello"

    em = EventManager(root_node=p)
    events = em.dispatch(
        {
            "_t": "ValueUpdateEvent",
            "ControlPath": "Root.ButtonChange",
            "Key": "Pressed",
            "Value": True,
        },
    )

    assert len(events) == 2
    assert events[0].control_path == "Root.ButtonChange"
    assert events[1].control_path == "Root.Text"
    assert events[1].value == "Changed"


def test_control_update_event(default_db_fixture):
    @dataclass(slots=True, kw_only=True, eq=False)
    class TestControlPanel(PanelControl):
        def init_content(self):
            text = TextControl(control_path="Text", value="Hello")
            self.attach_control(text)

            change_button = ButtonControl(
                control_path="ButtonChange",
            )
            self.attach_control(change_button)

        def on_change(self, control_path: str, key: str, value: Any) -> list[ControlEvent]:
            events = []
            if control_path == "Root.ButtonChange" and key == "pressed":
                text = self.load_child("Text", TextControl)
                events += text.update_control(**{"value": "Changed", "wrap_lines": False})

            return events

    p = TestControlPanel(control_path="Root", view_for="Something", view_name="TestPanel")
    p.init_content()
    TypeInfo._add_type(TestControlPanel)

    ControlSaver(root_node=p.build()).save()
    loaded = ControlLoader(root_node=p.get_key().build()).load()

    assert loaded[1].control_path == "Root.Text"
    assert loaded[1].value == "Hello"

    em = EventManager(root_node=p)
    events = em.dispatch(
        {
            "_t": "ValueUpdateEvent",
            "ControlPath": "Root.ButtonChange",
            "Key": "Pressed",
            "Value": True,
        },
    )

    assert len(events) == 2
    assert events[0].control_path == "Root.ButtonChange"
    assert events[1].control_path == "Root.Text"
    assert isinstance(events[1], ControlUpdateEvent)
    assert events[1].control["_t"] == "TextControl"
    assert events[1].control["Value"] == "Changed"
    assert events[1].control["WrapLines"] == False
