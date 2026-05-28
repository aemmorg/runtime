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
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.freeze_util import FreezeUtil
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.serializers.data_serializers import DataSerializers
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_composite import StubDataclassComposite
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_double_derived import StubDataclassDoubleDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import StubDataclassListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_optional_fields import StubDataclassOptionalFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_other_derived import StubDataclassOtherDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic import StubDataclassPolymorphic
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields import StubDataclassPrimitiveFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_singleton import StubDataclassSingleton


def test_data_serialization():
    sample_types = [
        StubDataclass,
        StubDataclassNestedFields,
        StubDataclassComposite,
        StubDataclassDerived,
        StubDataclassDoubleDerived,
        StubDataclassOtherDerived,
        StubDataclassListFields,
        # StubDataclassTupleFields,
        StubDataclassOptionalFields,
        # TODO (Roman): Uncomment when serialization format supports all dict value types
        # StubDataclassDictFields,
        # StubDataclassDictListFields,
        # StubDataclassListDictFields,
        StubDataclassPrimitiveFields,
        StubDataclassSingleton,
        # StubDataclassAnyFields,  TODO (Roman): Uncomment when supported consistent Any ui serialization.
        StubDataclassPolymorphic,
    ]

    for sample_type in sample_types:
        sample = sample_type().build()
        serialized = DataSerializers.FOR_UI.serialize(sample)
        deserialized = DataSerializers.FOR_UI.deserialize(serialized)
        assert deserialized == FreezeUtil.freeze(sample)

        # Record in RegressionGuard
        result_str = BootstrapSerializers.YAML.serialize(serialized)
        guard = RegressionGuard(prefix=sample_type.__name__).build()
        guard.write(result_str)
    RegressionGuard.verify_all()


def test_null_fields_inclusion():
    """Test correct None fields inclusion in UI serialized data."""
    sample = StubDataclassOptionalFields().build()
    serialized = DataSerializers.FOR_UI.serialize(sample)
    # Check that fields with None value are included
    assert [key for key in serialized if serialized[key] is None]


def test_positional_dict_keys_preserved():
    """Positional index keys like "_0" (used by panel layouts, cell styles) must survive UI (de)serialization."""
    serializer = DataSerializers.FOR_UI

    # Positional keys are passed through unchanged in both directions (a leading underscore before a
    # digit is not valid snake_case and would otherwise raise during PascalCase conversion).
    for key in ("_0", "_1", "_12"):
        assert serializer._serialize_key(key) == key
        assert serializer._deserialize_key(key) == key

    # Regular field keys are still PascalCase-converted on the wire and back.
    assert serializer._serialize_key("my_field") == "MyField"
    assert serializer._deserialize_key("MyField") == "my_field"


if __name__ == "__main__":
    pytest.main([__file__])
