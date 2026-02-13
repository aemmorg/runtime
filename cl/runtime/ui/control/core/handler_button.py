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
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.ui.control.core.button import Button
from cl.runtime.ui.control.handler_button_control import HandlerParameters


@dataclass(slots=True, kw_only=True)
class HandlerButton(Button):
    """Handler button action definition. Defines button label and icon (if needed) and handler parameters."""

    handler_params: HandlerParameters = required()
    """Parameters to call a handler with /run route."""
