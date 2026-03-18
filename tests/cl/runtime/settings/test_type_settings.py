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
from stubs.cl.runtime.settings.stub_type_name_rule import StubTypeNameRule


def test_type_settings():
    """Test that TypeSettings loads type_name_rules from cl.runtime.settings.yaml and applies them correctly."""

    # Qualname of the stub class used to test the rule
    stub_qual_name = "stubs.cl.runtime.settings.stub_type_name_rule.StubTypeNameRule"

    # Verify the rule defined in cl.runtime.settings.yaml is loaded
    settings = TypeSettings.instance(package="cl.runtime")
    assert settings.type_name_rules is not None
    assert "stubs.cl.runtime.settings.stub_type_name_rule.{ClassName}" in settings.type_name_rules

    # Verify get_type_name_rules includes the rule from cl.runtime
    rules = TypeSettings.get_type_name_rules()
    assert len(rules) > 0
    assert ("stubs.cl.runtime.settings.stub_type_name_rule.{ClassName}", "{ClassName}Override") in rules

    # Verify get_type_name matches the stub qualname and applies the Override suffix
    assert TypeSettings.get_type_name(stub_qual_name) == StubTypeNameRule.__name__ + "Override"

    # Verify qualname outside all patterns falls back to class name
    assert TypeSettings.get_type_name("some.other.package.MyClass") == "MyClass"


if __name__ == "__main__":
    pytest.main([__file__])
