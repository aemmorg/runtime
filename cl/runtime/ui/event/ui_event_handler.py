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

from __future__ import annotations
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Generic
from typing import TypeVar
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.ui.event.ui_event import UiEvent

T = TypeVar("T", bound=UiEvent)


@dataclass(slots=True, kw_only=True)
class UiEventHandler(ABC, Generic[T]):
    @abstractmethod
    def process(self, target: DataMixin, event: T) -> list[UiEvent]:
        """Process events on a target (Control or InteractiveMixin record)."""
