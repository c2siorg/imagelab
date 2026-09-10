from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GraphCycleError(ValueError):
    """Exception raised when a cycle is detected in a graph."""

    def __init__(self, cycle: list[str]):
        self.cycle = cycle
        if len(cycle) >= 2:
            from_node = cycle[-2]
            to_node = cycle[-1]
            message = (
                f"Cycle detected: {' -> '.join(cycle)}. "
                f"Removing the connection between {from_node} and {to_node} would fix this."
            )
        else:
            message = f"Cycle detected: {' -> '.join(cycle)}." if cycle else "Cycle detected."
        super().__init__(message)


class GraphNode(BaseModel):
    id: str
    type: str | None = None
    op: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    # Control-flow nodes own nested graphs.  Blockly input names are deliberately
    # not represented here: the UI serializer maps them to canonical names.
    branches: dict[str, "PipelineGraph"] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_type_or_op(self) -> "GraphNode":
        if not self.type and not self.op:
            raise ValueError("Either 'type' or 'op' must be specified for a node.")
        if self.type and not self.op:
            self.op = self.type
        elif self.op and not self.type:
            self.type = self.op
        return self


class GraphEdge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    input_port: str | None = None


class PipelineGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]

    @model_validator(mode="after")
    def validate_graph_structure(self) -> "PipelineGraph":
        node_ids = {n.id for n in self.nodes}
        if len(node_ids) != len(self.nodes):
            seen = set()
            duplicates = []
            for n in self.nodes:
                if n.id in seen:
                    duplicates.append(n.id)
                seen.add(n.id)
            raise ValueError(f"Duplicate node IDs found in graph: {list(set(duplicates))}")

        for edge in self.edges:
            if edge.from_node not in node_ids:
                raise ValueError(f"Edge references non-existent 'from' node: {edge.from_node}")
            if edge.to_node not in node_ids:
                raise ValueError(f"Edge references non-existent 'to' node: {edge.to_node}")
        return self

    def find_cycle(self) -> list[str] | None:
        """
        Detect cycles in the graph using DFS with white (0), gray (1), and black (2) coloring.
        If a cycle is found, returns the cycle path as a list of node IDs.
        Returns None otherwise.
        """
        # 0 = white, 1 = gray, 2 = black
        state = {n.id: 0 for n in self.nodes}
        adj = {n.id: [] for n in self.nodes}
        for edge in self.edges:
            adj[edge.from_node].append(edge.to_node)

        path_stack = []

        def dfs(u: str) -> list[str] | None:
            state[u] = 1
            path_stack.append(u)

            # Keep traversal deterministic
            for v in adj[u]:
                if state[v] == 1:
                    # Found back-edge u -> v
                    idx = path_stack.index(v)
                    return path_stack[idx:] + [v]
                elif state[v] == 0:
                    cycle = dfs(v)
                    if cycle is not None:
                        return cycle

            path_stack.pop()
            state[u] = 2
            return None

        # Sort nodes by ID for deterministic cycle detection start order
        sorted_nodes = sorted([n.id for n in self.nodes])
        for node_id in sorted_nodes:
            if state[node_id] == 0:
                cycle = dfs(node_id)
                if cycle is not None:
                    return cycle
        return None

    def validate_no_cycles(self) -> None:
        """
        Checks the graph for cycles.
        Raises GraphCycleError if a cycle is detected.
        """
        cycle = self.find_cycle()
        if cycle:
            raise GraphCycleError(cycle)


class KahnSorter:
    """
    Kahn's algorithm state tracker for topological sorting.
    Exposes the ready queue for dynamic scheduling.
    """

    def __init__(self, graph: PipelineGraph):
        self.graph = graph
        self.in_degree = {n.id: 0 for n in graph.nodes}
        self.adj = {n.id: [] for n in graph.nodes}

        for edge in graph.edges:
            self.adj[edge.from_node].append(edge.to_node)
            self.in_degree[edge.to_node] += 1

        # Deterministic order for ready nodes
        self.ready_queue = sorted([n.id for n in graph.nodes if self.in_degree[n.id] == 0])
        self.completed = set()

    def get_ready(self) -> list[str]:
        """Returns the list of node IDs currently in the ready queue."""
        return list(self.ready_queue)

    def pop_ready(self) -> str:
        """Pops a node from the ready queue."""
        if not self.ready_queue:
            raise IndexError("pop from an empty ready queue")
        return self.ready_queue.pop(0)

    def mark_complete(self, node_id: str) -> list[str]:
        """
        Marks a node as completed, decrements the in-degree of its outgoing neighbors,
        and adds newly ready nodes to the ready queue.
        Returns the list of newly ready node IDs.
        """
        if node_id not in self.in_degree:
            raise ValueError(f"Node {node_id} does not exist in the graph.")
        if node_id in self.completed:
            return []

        self.completed.add(node_id)
        if node_id in self.ready_queue:
            self.ready_queue.remove(node_id)

        newly_ready = []
        for neighbor in self.adj[node_id]:
            if neighbor in self.completed:
                continue
            self.in_degree[neighbor] -= 1
            if self.in_degree[neighbor] == 0:
                newly_ready.append(neighbor)

        newly_ready.sort()
        self.ready_queue.extend(newly_ready)
        return newly_ready

    def has_pending(self) -> bool:
        """Returns True if there are remaining uncompleted nodes."""
        return len(self.completed) < len(self.graph.nodes)


def topological_sort(graph: PipelineGraph) -> list[str]:
    """
    Performs topological sort on the graph using Kahn's algorithm.
    Runs DFS-based cycle check as a separate first pass.
    Raises GraphCycleError if a cycle is found.
    """
    graph.validate_no_cycles()

    sorter = KahnSorter(graph)
    result = []
    while sorter.ready_queue:
        node_id = sorter.pop_ready()
        result.append(node_id)
        sorter.mark_complete(node_id)

    if sorter.has_pending():
        raise GraphCycleError([])

    return result
