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

from collections import defaultdict
from collections import deque
from dataclasses import dataclass
from typing import Any
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.typename import typename
from cl.runtime.ui.control.control import Control
from cl.runtime.ui.control.control_container import ControlContainer
from cl.runtime.ui.control.dag_control_edge import DagControlEdge
from cl.runtime.ui.control.dag_node_control import DagNodeControl
from cl.runtime.ui.event.ui_event import UiEvent


@dataclass(slots=True, kw_only=True)
class DagControl(ControlContainer):
    """Container for DAG visualization with nodes and edges."""

    dag_nodes: list[str] = required(default_factory=list)
    """List of node IDs in the DAG (each is a control_path segment of a child DagNodeControl)."""

    dag_edges: list[DagControlEdge] = required(default_factory=list)
    """List of edges connecting nodes in the DAG."""

    def attach_control(self, control: Control) -> None:
        """Override to populate dag_nodes when attaching a DagNodeControl."""
        if not isinstance(control, DagNodeControl):
            raise UserError(
                f"DagControl only accepts {typename(DagNodeControl)} children, got {typename(type(control))}."
            )
        super(DagControl, self).attach_control(control)
        self.dag_nodes = list(self.dag_nodes)
        self.dag_nodes.append(self._get_node_id(control.control_path))

    def remove_control(self, control_path: str) -> None:
        """Override to remove the node ID from dag_nodes and clean up connected edges."""
        super(DagControl, self).remove_control(control_path)
        node_id = self._get_node_id(control_path)
        self.dag_nodes = [n for n in self.dag_nodes if n != node_id]
        self.dag_edges = [e for e in self.dag_edges if e.source != node_id and e.target != node_id]

    def update_control(self, **kwargs) -> list[UiEvent]:
        """Override to prevent direct modification of dag_nodes and validate edges."""
        if "dag_nodes" in kwargs:
            raise UserError("Cannot modify dag_nodes directly. Use attach_control and remove_control instead.")
        if "dag_edges" in kwargs:
            self.validate(edges=kwargs["dag_edges"])
        return super(DagControl, self).update_control(**kwargs)

    def update_layout(self) -> list[UiEvent]:
        """Override to include dag_nodes and dag_edges changes in the layout update."""
        self.validate()
        events = super(DagControl, self).update_layout()
        events.append(self._create_value_update_event("dag_nodes", self.dag_nodes))
        events.append(self._create_value_update_event("dag_edges", self.dag_edges))
        return events

    def update_value(self, field: str, value: Any) -> list[UiEvent]:
        """Override to prevent direct modification of dag_nodes and validate edges."""
        if field == "dag_nodes":
            raise UserError("Cannot modify dag_nodes directly. Use attach_control and remove_control instead.")
        if field == "dag_edges":
            self.validate(edges=value)
        return super(DagControl, self).update_value(field, value)

    def update_partial_value(self, field: str, value: Any, index: str) -> list[UiEvent]:
        """Override to prevent direct modification of dag_nodes and validate edges."""
        if field == "dag_nodes":
            raise UserError("Cannot modify dag_nodes directly. Use attach_control and remove_control instead.")
        elif field == "dag_edges":
            # Simulate the partial update and validate before persisting
            index_parts = index.split(".")
            updated_edges = self._set_nested_value(list(self.dag_edges), index_parts, value, field)
            self.validate(edges=updated_edges)
        return super(DagControl, self).update_partial_value(field, value, index)

    def validate(self, edges: list[DagControlEdge] | None = None) -> None:
        """Validate the DAG."""
        self._validate_edges(edges)
        self._validate_no_cycles(edges)

    def _validate_edges(self, edges: list[DagControlEdge] | None = None) -> None:
        """Validate that all edge references exist and the graph has no cycles."""
        edges_ = edges if edges is not None else (self.dag_edges or [])
        if not edges_:
            return

        # Check that all edge endpoints exist in dag_nodes
        node_ids = frozenset(self.dag_nodes)
        for edge in edges_:
            if edge.source not in node_ids:
                raise UserError(f"Edge source '{edge.source}' does not exist in dag_nodes.")
            if edge.target not in node_ids:
                raise UserError(f"Edge target '{edge.target}' does not exist in dag_nodes.")

    def _validate_no_cycles(self, edges: list[DagControlEdge] | None = None) -> None:
        """Validate that edges form a DAG (no cycles) using Kahn's algorithm."""
        edges_ = edges if edges is not None else (self.dag_edges or [])
        if not edges_:
            return

        # Build adjacency list and in-degree map
        in_degree: dict[str, int] = defaultdict(int)
        adjacency: dict[str, list[str]] = defaultdict(list)
        for node_id in self.dag_nodes:
            in_degree[node_id] = 0
        for edge in edges_:
            adjacency[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        # Start with nodes that have no incoming edges
        queue = deque(node_id for node_id, degree in in_degree.items() if degree == 0)
        visited_count = 0

        # Process nodes in topological order
        while queue:
            node_id = queue.popleft()
            visited_count += 1
            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If not all nodes were visited, there is a cycle
        if visited_count != len(self.dag_nodes):
            raise UserError("DAG contains a cycle.")

    def _get_node_id(self, control_path: str) -> str:
        """Get node ID from control path."""
        return control_path.replace(self.control_path + ".", "", 1)

    def init_content(self):
        """Populate container with child node controls."""

    def get_control_type(self) -> str:
        return DagControl.__name__
