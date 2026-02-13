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
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.ui.control.configs.button_config import ButtonConfig


@dataclass(slots=True, kw_only=True)
class Button(DataclassMixin):
    """Descriptor for a UI button action."""

    id: str = required()
    """Unique identifier for the button action."""

    label: str = required()
    """Visible label; when None, a renderer fall back to an icon or button ID."""

    config: ButtonConfig | None = None
    """Configuration that customizes the button's appearance and behavior."""
