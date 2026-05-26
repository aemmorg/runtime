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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.qa.qa_client import QaClient
from cl.runtime.routers.storage.key_request_item import KeyRequestItem
from cl.runtime.routers.storage.save_request import SaveRequest
from cl.runtime.routers.storage.save_response_util import SaveResponseUtil
from cl.runtime.schema.module_decl_key import ModuleDeclKey
from cl.runtime.schema.type_decl_key import TypeDeclKey
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.ui.ui_app_state import UiAppState
from cl.runtime.ui.ui_app_state_key import UiAppStateKey
from cl.runtime.ui.ui_type_layout import UiTypeLayout
from cl.runtime.ui.ui_type_layout_key import UiTypeLayoutKey
from cl.runtime.ui.ui_type_state import UiTypeState
from cl.runtime.ui.ui_type_state_key import UiTypeStateKey

_UI_SERIALIZER = DataSerializers.FOR_UI


def _ui_app_state_payload_without_user() -> dict:
    """Build a UiAppState payload that contains no 'User' field (key schema no longer includes user)."""
    record = UiAppState(
        id="alice",
        application_name="Test App",
        application_theme="Dark",
    ).build()
    payload = _UI_SERIALIZER.serialize(record)
    # Sanity check: serialized payload must not carry a 'User' field — the schema dropped it.
    assert "User" not in payload
    return payload


def _ui_type_state_payload_without_user() -> dict:
    """Build a UiTypeState payload that contains no 'User' field."""
    record = UiTypeState(
        type_=TypeDeclKey(module=ModuleDeclKey().build(), name="UiAppState").build(),
        read_only=False,
        page_size=100,
    ).build()
    payload = _UI_SERIALIZER.serialize(record)
    assert "User" not in payload
    return payload


def _ui_type_layout_payload_without_user() -> dict:
    """Build a UiTypeLayout payload that contains no 'User' field."""
    record = UiTypeLayout(
        type_=TypeDeclKey(module=ModuleDeclKey().build(), name="UiAppState").build(),
        maximized_tab_id="Editor",
    ).build()
    payload = _UI_SERIALIZER.serialize(record)
    assert "User" not in payload
    return payload


def test_save_ui_app_state_without_user(default_db_fixture):
    """/storage/save accepts a UiAppState payload that omits the (removed) 'User' field."""
    payload = _ui_app_state_payload_without_user()

    result = SaveResponseUtil.save_records(SaveRequest(records=[payload]))

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], KeyRequestItem)
    assert result[0].key == "alice"

    loaded = active(DataSource).load_one(UiAppStateKey(id="alice").build(), cast_to=UiAppState)
    assert loaded is not None
    assert loaded.id == "alice"
    assert loaded.application_name == "Test App"
    assert loaded.application_theme == "Dark"


def test_save_ui_app_state_with_default(default_db_fixture):
    """A UiAppState payload missing both 'User' and 'Id' is built with id='default' via __init."""
    payload = {
        "_t": "UiAppState",
        "ApplicationName": "Default App",
        "ApplicationTheme": "Light",
    }

    result = SaveResponseUtil.save_records(SaveRequest(records=[payload]))

    assert len(result) == 1
    # __init populates id with 'default' when not provided.
    assert result[0].key == "default"

    loaded = active(DataSource).load_one(UiAppStateKey(id="default").build(), cast_to=UiAppState)
    assert loaded is not None
    assert loaded.id == "default"
    assert loaded.application_name == "Default App"


def test_save_ui_type_state_without_user(default_db_fixture):
    """/storage/save accepts a UiTypeState payload that omits the (removed) 'User' field."""
    payload = _ui_type_state_payload_without_user()

    result = SaveResponseUtil.save_records(SaveRequest(records=[payload]))

    assert len(result) == 1
    assert isinstance(result[0], KeyRequestItem)

    type_key = TypeDeclKey(module=ModuleDeclKey().build(), name="UiAppState").build()
    loaded = active(DataSource).load_one(UiTypeStateKey(type_=type_key).build(), cast_to=UiTypeState)
    assert loaded is not None
    assert loaded.type_.name == "UiAppState"
    assert loaded.read_only is False
    assert loaded.page_size == 100


def test_save_ui_type_layout_without_user(default_db_fixture):
    """/storage/save accepts a UiTypeLayout payload that omits the (removed) 'User' field."""
    payload = _ui_type_layout_payload_without_user()

    result = SaveResponseUtil.save_records(SaveRequest(records=[payload]))

    assert len(result) == 1
    assert isinstance(result[0], KeyRequestItem)

    type_key = TypeDeclKey(module=ModuleDeclKey().build(), name="UiAppState").build()
    loaded = active(DataSource).load_one(UiTypeLayoutKey(type_=type_key).build(), cast_to=UiTypeLayout)
    assert loaded is not None
    assert loaded.type_.name == "UiAppState"
    assert loaded.maximized_tab_id == "Editor"


def test_save_ui_types_api_without_user(default_db_fixture):
    """Hit the REST /storage/save endpoint for all three UI state types without a 'User' field."""
    payloads = [
        _ui_app_state_payload_without_user(),
        _ui_type_state_payload_without_user(),
        _ui_type_layout_payload_without_user(),
    ]

    with QaClient() as client:
        for payload in payloads:
            response = client.post("/storage/save", json=[payload])
            assert response.status_code == 200, response.text
            body = response.json()
            assert isinstance(body, list)
            assert len(body) == 1
            assert body[0].get("Key") is not None


if __name__ == "__main__":
    pytest.main([__file__])
