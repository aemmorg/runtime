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
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.ui.control.core.button import Button


@dataclass(slots=True, kw_only=True)
class ButtonContainer(DataclassMixin):
    """Lightweight container describing a group of buttons or a tooltip payload."""

    tooltip: bool = False
    """When True the container should be rendered as a tooltip."""

    text: str | None = None
    """Optional text displayed in the tooltip or container header."""

    buttons: list[Button] | None = None
    """Optional list of Button objects contained in this container."""
