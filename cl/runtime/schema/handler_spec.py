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

from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.schema.handler_param_spec import HandlerParamSpec
from cl.runtime.schema.type_hint import TypeHint


@dataclass(slots=True, kw_only=True)
class HandlerSpec(BootstrapMixin):
    """Handler specification replacing the deprecated HandlerDeclareDecl."""

    name: str
    """PascalCase handler name (e.g. "RunSomething")."""

    type_: str
    """Handler type: "job", "viewer", "process", or "content"."""

    comment: str | None = None
    """Docstring for the handler."""

    static: bool | None = None
    """True if classmethod/staticmethod."""

    params: list[HandlerParamSpec] | None = None
    """Handler parameters."""

    return_type: TypeHint | None = None
    """Return type hint for the handler."""

    label: str | None = None
    """Display label for the handler."""

    hidden: bool | None = None
    """If True, handler is hidden in the UI."""

    def __init(self) -> None:
        """Set label from name when not explicitly provided (invoked by build())."""
        if self.label is None:
            self.label = CaseUtil.pascal_to_title_case(self.name)
