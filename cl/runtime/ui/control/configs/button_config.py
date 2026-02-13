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
from cl.runtime.ui.control.core.anchor_position import AnchorPosition
from cl.runtime.ui.control.core.button_icon import ButtonIcon
from cl.runtime.ui.control.core.button_type import ButtonType


@dataclass(slots=True, kw_only=True)
class ButtonConfig(DataclassMixin):
    """Configuration for how a button is presented and behaves."""

    help: str | None = None
    """Short help text or tooltip shown on hover."""

    icon: ButtonIcon | None = None
    """Icon identifier to render inside the button."""

    width: str | None = "content"
    """Width hint: "content", "stretch" or a pixel value like "200px"."""

    type: ButtonType | None = ButtonType.PRIMARY
    """Semantic button type used to choose styling."""

    position: AnchorPosition | None = AnchorPosition.TOP_LEFT
    """Anchor position hint for placement within a layout."""
