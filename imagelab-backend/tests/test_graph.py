import pytest
from pydantic import ValidationError

from app.models.graph import GraphCycleError, GraphEdge, GraphNode, KahnSorter, PipelineGraph, topological_sort


def test_empty_graph():
    graph = PipelineGraph(nodes=[], edges=[])
    assert topological_sort(graph) == []
    assert graph.find_cycle() is None


def test_single_node_graph():
    graph = PipelineGraph(nodes=[GraphNode(id="node_1", type="canny", params={})], edges=[])
    assert topological_sort(graph) == ["node_1"]
    assert graph.find_cycle() is None


def test_valid_types_or_op():
    # Both type and op can be used, validator makes sure they sync
    n1 = GraphNode(id="n1", type="canny")
    assert n1.op == "canny"

    n2 = GraphNode(id="n2", op="blur")
    assert n2.type == "blur"

    # Missing both raises error
    with pytest.raises(ValidationError):
        GraphNode(id="n3")


def test_invalid_graph_structure():
    # Duplicate node IDs
    with pytest.raises(ValidationError, match="Duplicate node IDs"):
        PipelineGraph(
            nodes=[
                GraphNode(id="n1", type="canny"),
                GraphNode(id="n1", type="blur"),
            ],
            edges=[],
        )

    # Edge references non-existent node
    with pytest.raises(ValidationError, match="Edge references non-existent 'from' node"):
        PipelineGraph(
            nodes=[GraphNode(id="n1", type="canny")], edges=[GraphEdge(**{"from": "non_existent", "to": "n1"})]
        )

    with pytest.raises(ValidationError, match="Edge references non-existent 'to' node"):
        PipelineGraph(
            nodes=[GraphNode(id="n1", type="canny")], edges=[GraphEdge(**{"from": "n1", "to": "non_existent"})]
        )


def test_cyclic_graph_dfs_path_simple():
    # Simple cycle: A -> B -> C -> A
    graph = PipelineGraph(
        nodes=[
            GraphNode(id="A", type="canny"),
            GraphNode(id="B", type="canny"),
            GraphNode(id="C", type="canny"),
        ],
        edges=[
            GraphEdge(**{"from": "A", "to": "B"}),
            GraphEdge(**{"from": "B", "to": "C"}),
            GraphEdge(**{"from": "C", "to": "A"}),
        ],
    )
    assert graph.find_cycle() == ["A", "B", "C", "A"]

    with pytest.raises(GraphCycleError) as excinfo:
        topological_sort(graph)

    assert excinfo.value.cycle == ["A", "B", "C", "A"]
    assert (
        str(excinfo.value)
        == "Cycle detected: A -> B -> C -> A. Removing the connection between C and A would fix this."
    )


def test_cyclic_graph_self_loop():
    # Self loop: A -> A
    graph = PipelineGraph(nodes=[GraphNode(id="A", type="canny")], edges=[GraphEdge(**{"from": "A", "to": "A"})])
    assert graph.find_cycle() == ["A", "A"]

    with pytest.raises(GraphCycleError) as excinfo:
        topological_sort(graph)

    assert excinfo.value.cycle == ["A", "A"]
    assert str(excinfo.value) == "Cycle detected: A -> A. Removing the connection between A and A would fix this."


def test_canny_histogram_merge_diamond():
    # The diamond example:
    #      input
    #      /   \
    # canny     histogram
    #      \   /
    #      merge
    graph = PipelineGraph(
        nodes=[
            GraphNode(id="input", type="read_image"),
            GraphNode(id="canny", type="filtering_canny"),
            GraphNode(id="histogram", type="histogram_operations"),
            GraphNode(id="merge", type="merge_images"),
        ],
        edges=[
            GraphEdge(**{"from": "input", "to": "canny"}),
            GraphEdge(**{"from": "input", "to": "histogram"}),
            GraphEdge(**{"from": "canny", "to": "merge"}),
            GraphEdge(**{"from": "histogram", "to": "merge"}),
        ],
    )

    order = topological_sort(graph)
    # The topological sort can be:
    # ["input", "canny", "histogram", "merge"] or ["input", "histogram", "canny", "merge"]
    assert order[0] == "input"
    assert order[-1] == "merge"
    assert set(order[1:3]) == {"canny", "histogram"}

    # Let's verify KahnSorter directly
    sorter = KahnSorter(graph)
    assert sorter.get_ready() == ["input"]

    node = sorter.pop_ready()
    assert node == "input"

    newly_ready = sorter.mark_complete(node)
    # Both canny and histogram become ready. Sorter sorts alphabetically so they are ['canny', 'histogram']
    assert newly_ready == ["canny", "histogram"]
    assert sorter.get_ready() == ["canny", "histogram"]

    node = sorter.pop_ready()
    assert node == "canny"
    newly_ready = sorter.mark_complete(node)
    assert newly_ready == []
    assert sorter.get_ready() == ["histogram"]

    node = sorter.pop_ready()
    assert node == "histogram"
    newly_ready = sorter.mark_complete(node)
    assert newly_ready == ["merge"]
    assert sorter.get_ready() == ["merge"]

    node = sorter.pop_ready()
    assert node == "merge"
    newly_ready = sorter.mark_complete(node)
    assert newly_ready == []
    assert sorter.get_ready() == []
    assert not sorter.has_pending()


def test_non_cyclic_fan_in_fan_out():
    # A more complex graph structure:
    # A -> B -> D
    # A -> C -> D
    # C -> E
    # F -> E
    # (A, F are sources; D, E are sinks)
    graph = PipelineGraph(
        nodes=[
            GraphNode(id="A", type="noop"),
            GraphNode(id="B", type="noop"),
            GraphNode(id="C", type="noop"),
            GraphNode(id="D", type="noop"),
            GraphNode(id="E", type="noop"),
            GraphNode(id="F", type="noop"),
        ],
        edges=[
            GraphEdge(**{"from": "A", "to": "B"}),
            GraphEdge(**{"from": "A", "to": "C"}),
            GraphEdge(**{"from": "B", "to": "D"}),
            GraphEdge(**{"from": "C", "to": "D"}),
            GraphEdge(**{"from": "C", "to": "E"}),
            GraphEdge(**{"from": "F", "to": "E"}),
        ],
    )

    order = topological_sort(graph)

    # Verify that the order satisfies topological constraints:
    # For every edge from -> to, from must precede to in the output list.
    positions = {node_id: idx for idx, node_id in enumerate(order)}
    for edge in graph.edges:
        assert positions[edge.from_node] < positions[edge.to_node]
