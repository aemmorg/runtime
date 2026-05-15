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
from cl.runtime.records.variant.str_variant import StrVariant
from cl.runtime.records.variant.text_container import TextContainer
from cl.runtime.records.variant.variant_util import VariantUtil
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.ui.control.button_control import ButtonControl
from cl.runtime.ui.control.configs.column_config import ColumnConfig
from cl.runtime.ui.control.panel_control import PanelControl
from cl.runtime.ui.control.table_control import TableControl
from cl.runtime.ui.control.text_control import TextControl
from cl.runtime.ui.control.tree_table_control import TreeTableControl
from cl.runtime.ui.event.control_update_event import ControlUpdateEvent
from cl.runtime.ui.event.event_manager import EventManager
from cl.runtime.ui.event.partial_value_update_event import PartialValueUpdateEvent
from cl.runtime.ui.event.ui_event import UiEvent
from cl.runtime.ui.resolver.control_target_resolver import ControlTargetResolver
from cl.runtime.ui.storage.control_loader import ControlLoader
from cl.runtime.ui.storage.control_saver import ControlSaver
from stubs.cl.runtime.views.stub_viewers_key import StubViewersKey

_STUB_KEY = StubViewersKey(stub_id="Something").build()


def test_partial_value_update_event(default_db_fixture, type_info_fixture):
    @dataclass(slots=True, kw_only=True, eq=False)
    class TestPartialValuePanel(PanelControl):
        def init_content(self):
            table = TableControl(
                control_path="table",
                col_names=["index", "string_element", "double_element"],
                data=[VariantUtil.create("Val1"), VariantUtil.create("Val2"), VariantUtil.create("Val3")],
            )
            table.init()
            self.attach_control(table)

            change_button = ButtonControl(
                control_path="button_change",
            )
            self.attach_control(change_button)

        def on_change(self, key: str, field: str, value: Any, index: str | None = None) -> list[UiEvent]:
            events = []
            if key == "root.button_change" and field == "pressed":
                table = self.load_child("table", TableControl)
                events += table.update_partial_value("data", VariantUtil.create("Changed"), "1")

            return events

    p = TestPartialValuePanel(control_path="root", view_for=_STUB_KEY, view_name="TestPanel")
    p.init_content()
    TypeInfo.register_type(TestPartialValuePanel)

    ControlSaver(root_node=p.build()).save()
    loaded = ControlLoader(root_node=p.get_key().build()).load()

    assert loaded[1].control_path == "root.table"
    assert loaded[1].data == (
        StrVariant(metadata=None, value="Val1"),
        StrVariant(metadata=None, value="Val2"),
        StrVariant(metadata=None, value="Val3"),
    )

    em = EventManager(resolver=ControlTargetResolver(key=_STUB_KEY, viewer_name="TestPanel"))
    events = em.dispatch(
        {
            "_t": "ValueUpdateEvent",
            "Key": "root.button_change",
            "Field": "Pressed",
            "Value": True,
        },
    )
    assert len(events) == 2
    assert isinstance(events[1], PartialValueUpdateEvent)
    assert events[1].key == "root.table"
    assert events[1].field == "Data"
    assert events[1].value == {"_t": "StrVariant", "Metadata": None, "Value": "Changed"}
    assert events[1].index == "1"


# TODO(Claude): Identify the reason for test failure, fix and remove skip
@pytest.mark.skip("Restore after the test is fixed.")
def test_nested_partial_value_update_event(default_db_fixture, type_info_fixture):
    """Test update_partial_value with nested index (e.g. '0.data.1') on TreeTableControl."""

    @dataclass(slots=True, kw_only=True, eq=False)
    class TestNestedPartialValuePanel(PanelControl):
        def init_content(self):
            table = TreeTableControl(
                control_path="tree_table",
                columns=[
                    ColumnConfig(label="Name"),
                    ColumnConfig(label="Value"),
                ],
                data=[
                    TextContainer(data=["row0", "row1", "row2"]),
                    TextContainer(data=["val0", "val1", "val2"]),
                ],
            )
            self.attach_control(table)

            change_button = ButtonControl(
                control_path="button_change",
            )
            self.attach_control(change_button)

        def on_change(self, key: str, field: str, value: Any, index: str | None = None) -> list[UiEvent]:
            events = []
            if key == "root.button_change" and field == "pressed":
                table = self.load_child("tree_table", TreeTableControl)
                # Update second column (index 1), row at index 2 -> nested index "1.data.2"
                events += table.update_partial_value("data", "Changed", "1.data.2")
            return events

    p = TestNestedPartialValuePanel(control_path="root", view_for=_STUB_KEY, view_name="TestPanel")
    p.init_content()
    TypeInfo.register_type(TestNestedPartialValuePanel)

    ControlSaver(root_node=p.build()).save()
    loaded = ControlLoader(root_node=p.get_key().build()).load()

    # Verify initial data
    tree_table = loaded[1]
    assert tree_table.control_path == "root.tree_table"
    assert tree_table.data[1].data == ("val0", "val1", "val2")

    em = EventManager(resolver=ControlTargetResolver(key=_STUB_KEY, viewer_name="TestPanel"))
    events = em.dispatch(
        {
            "_t": "ValueUpdateEvent",
            "Key": "root.button_change",
            "Field": "Pressed",
            "Value": True,
        },
    )

    assert len(events) == 2
    assert isinstance(events[1], PartialValueUpdateEvent)
    assert events[1].key == "root.tree_table"
    assert events[1].field == "Data"
    assert events[1].value == "Changed"
    assert events[1].index == "1.data.2"

    # Verify the data was actually persisted with the nested update
    reloaded = ControlLoader(root_node=p.get_key().build()).load()
    reloaded_table = reloaded[1]
    assert reloaded_table.data[1].data[2] == "Changed"
    # Other values unchanged
    assert reloaded_table.data[1].data[0] == "val0"
    assert reloaded_table.data[1].data[1] == "val1"
    assert reloaded_table.data[0].data == ("row0", "row1", "row2")


def test_value_update_event(default_db_fixture, type_info_fixture):
    @dataclass(slots=True, kw_only=True, eq=False)
    class TestValuePanel(PanelControl):
        def init_content(self):
            text = TextControl(control_path="text", value="Hello")
            self.attach_control(text)

            change_button = ButtonControl(
                control_path="button_change",
            )
            self.attach_control(change_button)

        def on_change(self, key: str, field: str, value: Any, index: str | None = None) -> list[UiEvent]:
            events = []
            if key == "root.button_change" and field == "pressed":
                text = self.load_child("text", TextControl)
                events += text.update_value("value", "Changed")

            return events

    p = TestValuePanel(control_path="root", view_for=_STUB_KEY, view_name="TestPanel")
    p.init_content()
    TypeInfo.register_type(TestValuePanel)

    ControlSaver(root_node=p.build()).save()
    loaded = ControlLoader(root_node=p.get_key().build()).load()

    assert loaded[1].control_path == "root.text"
    assert loaded[1].value == "Hello"

    em = EventManager(resolver=ControlTargetResolver(key=_STUB_KEY, viewer_name="TestPanel"))
    events = em.dispatch(
        {
            "_t": "ValueUpdateEvent",
            "Key": "root.button_change",
            "Field": "Pressed",
            "Value": True,
        },
    )

    assert len(events) == 2
    assert events[0].key == "root.button_change"
    assert events[1].key == "root.text"
    assert events[1].value == "Changed"


def test_control_update_event(default_db_fixture, type_info_fixture):
    @dataclass(slots=True, kw_only=True, eq=False)
    class TestControlPanel(PanelControl):
        def init_content(self):
            text = TextControl(control_path="text", value="Hello")
            self.attach_control(text)

            change_button = ButtonControl(
                control_path="button_change",
            )
            self.attach_control(change_button)

        def on_change(self, key: str, field: str, value: Any, index: str | None = None) -> list[UiEvent]:
            events = []
            if key == "root.button_change" and field == "pressed":
                text = self.load_child("text", TextControl)
                events += text.update_control(**{"value": "Changed", "wrap_lines": False})

            return events

    p = TestControlPanel(control_path="root", view_for=_STUB_KEY, view_name="TestPanel")
    p.init_content()
    TypeInfo.register_type(TestControlPanel)

    ControlSaver(root_node=p.build()).save()
    loaded = ControlLoader(root_node=p.get_key().build()).load()

    assert loaded[1].control_path == "root.text"
    assert loaded[1].value == "Hello"

    em = EventManager(resolver=ControlTargetResolver(key=_STUB_KEY, viewer_name="TestPanel"))
    events = em.dispatch(
        {
            "_t": "ValueUpdateEvent",
            "Key": "root.button_change",
            "Field": "Pressed",
            "Value": True,
        },
    )

    assert len(events) == 2
    assert events[0].key == "root.button_change"
    assert events[1].key == "root.text"
    assert isinstance(events[1], ControlUpdateEvent)
    assert events[1].control["_t"] == "TextControl"
    assert events[1].control["Value"] == "Changed"
    assert events[1].control["WrapLines"] == False


if __name__ == "__main__":
    pytest.main([__file__])
