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
from cl.runtime.settings.type_settings import TypeSettings


def test_type_settings():
    """Test that TypeSettings loads type_name_rules from cl.runtime.settings.yaml and applies them correctly."""

    # Qualnames of the stub classes used to test the rule
    original_qual_name = (
        "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_with_custom_name.StubDataclassWithCustomName"
    )
    override_qual_name = (
        "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_with_custom_name_override.StubDataclassWithCustomName"
    )

    # Verify the rule defined in cl.runtime.settings.yaml is loaded
    settings = TypeSettings.instance(package="cl.runtime")
    assert settings.type_name_rules is not None
    assert (
        "stubs.cl.runtime.records.for_dataclasses.{module_name}.StubDataclassWithCustomName" in settings.type_name_rules
    )

    # Verify get_type_name_rules includes the rule from cl.runtime
    rules = TypeSettings.get_type_name_rules()
    assert len(rules) > 0
    assert (
        "stubs.cl.runtime.records.for_dataclasses.{module_name}.StubDataclassWithCustomName",
        "{module_name}",
    ) in rules

    # Verify the original class gets its default name (module snake_case converts to PascalCase matching class name)
    assert TypeSettings.get_type_name(original_qual_name) == "StubDataclassWithCustomName"

    # Verify the override class gets an overridden name (module snake_case converts to PascalCase with Override suffix)
    assert TypeSettings.get_type_name(override_qual_name) == "StubDataclassWithCustomNameOverride"

    # Verify qualname outside all patterns falls back to class name
    assert TypeSettings.get_type_name("some.other.package.MyClass") == "MyClass"


if __name__ == "__main__":
    pytest.main([__file__])
