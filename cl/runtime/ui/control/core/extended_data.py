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


@dataclass(slots=True, kw_only=True)
class ExtendedData(DataclassMixin):
    """
    Auxiliary data item used in table displays.
    Represents an id/label pair with optional metadata that can be attached to table cell or other UI elements.
    """

    id: str = required()
    """Stable identifier for the data item."""

    label: str | None = None
    """Human-readable label for display purposes."""

    meta: str | None = None  # TODO: Migrate on alternative of Any after system support
    """Optional free-form metadata associated with the item."""
