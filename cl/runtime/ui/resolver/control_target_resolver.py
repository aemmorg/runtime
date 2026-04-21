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
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.ui.control import Control
from cl.runtime.ui.control.control_key import ControlKey
from cl.runtime.ui.resolver.target_resolver import TargetResolver
from cl.runtime.ui.storage.control_loader import ControlLoader


@dataclass(slots=True, kw_only=True)
class ControlTargetResolver(TargetResolver[Control]):
    """Resolves Controls by ControlPath via ControlLoader."""

    key: KeyMixin = required()
    """Key of the record for which the control is displayed."""

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
            root_key = ControlKey(view_for=self.key, view_name=self.viewer_name, control_path="root")
            self._root_node = active(DataSource).load_one_or_none(root_key.build())
            if self._root_node is None:
                raise RuntimeError("Root node is missing")
