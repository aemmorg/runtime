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
from cl.runtime.records.record_panel import RecordPanel
from cl.runtime.records.typename import typename
from cl.runtime.records.ui_record_util import UiRecordUtil
from cl.runtime.schema.handler_declare_decl import HandlerDeclareDecl
from cl.runtime.views.empty_view import EmptyView
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_data import StubDataclassData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_handlers import StubHandlers
from stubs.cl.runtime.views.stub_data_viewers import StubDataViewers


def test_panel_kind():
    """Test panel kinds."""

    # Test that _get_panel_kind returns 'Primary' for dynamic view with name 'self'
    handler = HandlerDeclareDecl(name="ViewSelf", label="Self", type_="Viewer").build()
    result = UiRecordUtil._get_primary_kind_or_none(handler)
    assert result == "Primary"

    # Test that _get_panel_kind returns None for dynamic view with name other than 'self'
    handler = HandlerDeclareDecl(name="ViewViewer", label="Viewer", type_="Viewer").build()
    result = UiRecordUtil._get_primary_kind_or_none(handler)
    assert result is None

    # Test that _get_panel_kind returns None for non-view handlers
    handler = HandlerDeclareDecl(name="ViewSelf", label="Self", type_="Job").build()
    result = UiRecordUtil._get_primary_kind_or_none(handler)
    assert result is None


def test_create_panels_from_handlers():
    """Test _create_panels_from_handlers."""

    # Test that _create_panels_from_handlers creates panels from viewer handlers
    result = UiRecordUtil._create_panels_from_handlers(StubDataViewers)
    assert len(result) > 0
    assert all(isinstance(panel, RecordPanel) for panel in result)
    assert all(panel.persistable is False for panel in result)
    assert any(panel.label == "Self" and panel.kind == "Primary" for panel in result)

    # Test that _create_panels_from_handlers returns empty list for type without viewer handlers
    result = UiRecordUtil._create_panels_from_handlers(StubDataclass)
    assert result == []


def test_get_panels_with_dynamic_views(default_db_fixture):
    """Test that run_get_record_panels."""

    # Test that run_get_record_panels returns panels for a record with viewer handlers
    stub_id = "test_with_viewers"
    stub_record = StubDataViewers(stub_id=stub_id).build()
    active(DataSource).insert_one(stub_record, commit=True)

    panels = UiRecordUtil.run_get_record_panels(type_name=typename(StubDataViewers), key=stub_id)
    assert isinstance(panels, list)
    assert len(panels) > 0
    assert all(isinstance(panel, RecordPanel) for panel in panels)
    assert all(panel.persistable is False for panel in panels)
    assert any(p.label == "Self" and p.kind == "Primary" for p in panels)

    # Test that run_get_record_panels returns empty list for a record without any views
    stub_id = "test_no_viewers"
    stub_record = StubHandlers(stub_id=stub_id).build()
    active(DataSource).insert_one(stub_record, commit=True)

    panels = UiRecordUtil.run_get_record_panels(type_name=typename(StubHandlers), key=stub_id)
    assert isinstance(panels, list)
    assert len(panels) == 0

    # Test that run_get_record_panels raises RuntimeError for non-record types
    with pytest.raises(RuntimeError, match="is not a record type"):
        UiRecordUtil.run_get_record_panels(type_name=typename(StubDataclassData), key="_")

@pytest.mark.skip("Skipped until load_query is not working properly")
def test_get_panels_with_persisted_views(default_db_fixture):
    """Test run_get_record_panels includes persisted views in the results."""

    # Create and save record for which views will be created
    stub_id = "test_with_persisted_views"
    stub_record = StubDataclass(id=stub_id).build()
    active(DataSource).insert_one(stub_record, commit=True)

    # Create and save persisted views for the record
    view1 = EmptyView(view_for=stub_record.get_key(), view_name="FirstView").build()
    view2 = EmptyView(view_for=stub_record.get_key(), view_name="SecondView").build()
    active(DataSource).insert_one(view1, commit=True)
    active(DataSource).insert_one(view2, commit=True)

    # Get panels
    panels = UiRecordUtil.run_get_record_panels(type_name=typename(StubDataclass), key=stub_id)

    # Verify that panels are returned
    assert isinstance(panels, list)
    assert len(panels) == 2

    # Check that all panels are persisted
    assert all(p.persistable is True for p in panels)

    # Verify FirstView panel
    custom_view_1_panel = next((p for p in panels if p.name == "FirstView"), None)
    assert custom_view_1_panel is not None
    assert custom_view_1_panel.label == "FirstView"
    assert custom_view_1_panel.kind is None

    # Verify SecondView panel
    custom_view_2_panel = next((p for p in panels if p.name == "SecondView"), None)
    assert custom_view_2_panel is not None
    assert custom_view_2_panel.label == "SecondView"
    assert custom_view_2_panel.kind is None


if __name__ == "__main__":
    pytest.main([__file__])
