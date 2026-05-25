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
from typing import Any
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.ui.event.ui_event import UiEvent


@dataclass(slots=True, kw_only=True)
class RecordUpdateEvent(UiEvent):
    """Event carrying a full candidate record for server-side validation without persistence.

    The handler delegates to InteractiveMixin.update_record(candidate). The hook returns:

    - On any failure: one UserErrorEvent per failing field, optionally followed by a
      RecordUpdateEvent carrying the candidate as it stands (un-normalized for failed fields).
    - On full success: a single RecordUpdateEvent with the normalized candidate.

    The DB is not modified in either case.
    """

    record: dict[str, Any] = required()
    "Full serialized record (dict with the '_t' type discriminator)."
