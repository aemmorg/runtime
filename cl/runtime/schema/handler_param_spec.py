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
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.schema.type_hint import TypeHint


@dataclass(slots=True, kw_only=True)
class HandlerParamSpec(BootstrapMixin):
    """Handler parameter specification replacing the deprecated HandlerParamDecl."""

    name: str
    """PascalCase parameter name."""

    type_hint: TypeHint
    """Type hint chain for the parameter (same TypeHint linked-list structure as FieldSpec uses)."""

    label: str | None = None
    """Display label for the parameter."""
