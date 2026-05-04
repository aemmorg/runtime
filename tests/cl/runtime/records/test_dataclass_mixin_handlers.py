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

"""Tests for DataclassMixin handler discovery and key-field flagging introduced for v2.0.0."""

import pytest
from cl.runtime.ui.ui_app_state import UiAppState
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_handlers import StubHandlers


def test_handlers_discovered_from_run_and_view_methods():
    """StubHandlers exposes run_* and view_* methods; DataSpec.handlers must be populated."""

    spec = StubHandlers.get_type_spec()
    assert spec.handlers is not None
    assert len(spec.handlers) > 0
    # Handler types are classified as job (run_) or viewer (view_)
    handler_types = {h.type_ for h in spec.handlers}
    assert handler_types.issubset({"job", "viewer"})
    # Handler names are PascalCase
    names = [h.name for h in spec.handlers]
    assert all(name and name[0].isupper() for name in names)
    # Each handler carries a label defaulted from its name
    assert all(h.label for h in spec.handlers)


def test_key_field_flagged_on_fieldspec():
    """Fields that are part of the record's key must have FieldSpec.key=True."""

    spec = StubDataclass.get_type_spec()
    # StubDataclass.id is the key
    id_field = next(f for f in spec.fields if f.field_name == "id")
    assert id_field.key is True


def test_non_key_field_not_flagged():
    """Fields not part of the key should not have key=True."""

    # Pick any record type with non-key fields
    spec = UiAppState.get_type_spec()
    non_key_fields = [f for f in spec.fields if f.field_name != "user"]  # user is the key
    # At least one non-key field exists
    assert len(non_key_fields) > 0
    assert all(f.key in (None, False) for f in non_key_fields)


if __name__ == "__main__":
    pytest.main([__file__])
