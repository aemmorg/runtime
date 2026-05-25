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
from dataclasses import dataclass
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.ui.control import Control
from cl.runtime.ui.control.control_key import ControlKey
from cl.runtime.ui.resolver.target_resolver import TargetResolver
from cl.runtime.ui.storage.control_loader import ControlLoader


@dataclass(slots=True, kw_only=True)
class ControlTargetResolver(TargetResolver[Control]):
    """Resolves Controls by ControlPath via ControlLoader, given a raw delimited key string."""

    key: str = required()
    """Raw delimited key string of the record for which the control is displayed."""

    type_name: str = required()
    """Record type name; used to resolve the key type for deserialization."""

    viewer_name: str = required()
    """Viewer name for ControlKey."""

    _root_node: Control | None = None
    """Cached root Control node, loaded lazily."""

    def resolve(self, target_id: str) -> Control:
        """Load Control by its path using ControlLoader from the cached root node."""
        # Ensure the root node is loaded from DB on first call
        self._ensure_root_node()
        # Load control hierarchy by path starting from the root node
        control_list = ControlLoader(
            root_node=self._root_node.get_key().clone(),
        ).load_by_path(control_path=target_id)
        if not control_list:
            raise RuntimeError(f"Control({target_id}) not found")
        return control_list[0]

    def _ensure_root_node(self) -> None:
        """Load root node on first call."""
        if self._root_node is None:
            record_type = TypeInfo.from_type_name(self.type_name)
            key_type = record_type.get_key_type()
            key_obj = KeySerializers.DELIMITED.deserialize(self.key, TypeHint.for_type(key_type)).build()
            root_key = ControlKey(view_for=key_obj, view_name=self.viewer_name, control_path="root")
            self._root_node = active(DataSource).load_one_or_none(root_key.build())
            if self._root_node is None:
                raise RuntimeError("Root node is missing")
