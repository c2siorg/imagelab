"""The sole compiler boundary for pipeline and macro graphs."""

import uuid

from sqlmodel import Session, select

from app.models.graph import GraphCycleError, GraphNode, PipelineGraph, topological_sort
from app.models.persistence import PipelineVersion
from app.models.pipeline import PipelineRequest, PipelineResponse, PipelineStep
from app.utils.image import decode_base64_image


class GraphTypeError(ValueError):
    pass


OPERATOR_PORT_SPECS: dict[str, dict[str | None, list[int]]] = {
    "imageconvertions_grayimage": {"image": [3, 4], None: [3, 4]},
    "imageconvertions_colortobinary": {"image": [3, 4], None: [3, 4]},
    "imageconvertions_graytobinary": {"image": [1], None: [1]},
    "imageconvertions_channelsplit": {"image": [3, 4], None: [3, 4]},
    "imageconvertions_hsvtobgr": {"image": [3], None: [3]},
    "imageconvertions_bgrtohsv": {"image": [3, 4], None: [3, 4]},
    "imageconvertions_bgrtolab": {"image": [3, 4], None: [3, 4]},
    "imageconvertions_labtobgr": {"image": [3], None: [3]},
    "imageconvertions_bgrtoycrcb": {"image": [3, 4], None: [3, 4]},
    "imageconvertions_ycrcbtobgr": {"image": [3], None: [3]},
    "thresholding_adaptivethreshold": {"image": [1], None: [1]},
    "thresholding_otsuthreshold": {"image": [1], None: [1]},
    "merge_images": {"image": [3, 4], "mask": [1]},
    "blend_images": {"image": [3, 4], "mask": [1]},
}
OPERATOR_OUTPUT_CHANNELS = {
    "imageconvertions_grayimage": 1,
    "imageconvertions_colortobinary": 1,
    "imageconvertions_graytobinary": 1,
    "imageconvertions_channelsplit": 1,
    "thresholding_applythreshold": 1,
    "thresholding_adaptivethreshold": 1,
    "thresholding_otsuthreshold": 1,
    "filtering_cannyedge": 3,
    "segmentation_watershed": 3,
    "transformation_distance": 1,
}
CONTROL_BRANCHES = {"macro_blend": ("left", "right"), "macro_if_else": ("then", "else")}


def _node_type(node: GraphNode) -> str:
    return node.type or node.op or ""


def _coerce_graph(payload: dict) -> PipelineGraph:
    """Accept legacy persisted ``{steps: [...]}`` linear pipeline versions."""
    if "nodes" in payload:
        # Convert PipelineStep objects to dict format if needed
        nodes_data = []
        for idx, node in enumerate(payload["nodes"]):
            if isinstance(node, PipelineStep):
                nodes_data.append(
                    {
                        "id": node.block_id or str(idx),
                        "type": node.type,
                        "params": node.params,
                        "branches": node.branches,
                    }
                )
            else:
                # Ensure nodes have IDs
                if isinstance(node, dict) and "id" not in node:
                    node = dict(node, id=str(idx))
                nodes_data.append(node)

        # Legacy fallback: map old param branch names to new branch structure
        graph = PipelineGraph.model_validate({"nodes": nodes_data, "edges": payload.get("edges", [])})
        nodes = []
        for node in graph.nodes:
            params = dict(node.params)
            branches = dict(node.branches)
            # Map legacy param branch names to branch structure
            if "op1_branch" in params:
                branches["left"] = params.pop("op1_branch")
            if "op2_branch" in params:
                branches["right"] = params.pop("op2_branch")
            if "if_branch" in params:
                branches["then"] = params.pop("if_branch")
            if "else_branch" in params:
                branches["else"] = params.pop("else_branch")
            nodes.append(node.model_copy(update={"params": params, "branches": branches}))
        return graph.model_copy(update={"nodes": nodes})
    raw_steps = payload.get("steps", [])
    steps = [PipelineStep.model_validate(step) for step in raw_steps]
    return PipelineGraph(
        nodes=[
            {"id": step.block_id or str(index), "type": step.type, "params": step.params}
            for index, step in enumerate(steps)
        ],
        edges=[
            {"from": steps[index].block_id or str(index), "to": steps[index + 1].block_id or str(index + 1)}
            for index in range(len(steps) - 1)
        ],
    )


def _macro_id(node: GraphNode) -> str | None:
    node_type = _node_type(node)
    if node_type == "macro_ref":
        value = node.params.get("macro_id")
        return str(value) if value else None
    if node_type.startswith("macro_") and node_type not in CONTROL_BRANCHES:
        return node_type.removeprefix("macro_")
    return None


def _namespace_graph(graph: PipelineGraph, prefix: str) -> PipelineGraph:
    nodes = []
    for node in graph.nodes:
        # Handle branch values that might be lists or PipelineGraph
        namespaced_branches = {}
        for name, branch in node.branches.items():
            if isinstance(branch, list):
                # Convert list to PipelineGraph and namespace it
                branch_graph = _coerce_graph({"nodes": branch, "edges": []})
                namespaced_branches[name] = _namespace_graph(branch_graph, prefix)
            elif isinstance(branch, PipelineGraph):
                namespaced_branches[name] = _namespace_graph(branch, prefix)
            else:
                namespaced_branches[name] = branch
        nodes.append(node.model_copy(update={"id": f"{prefix}:{node.id}", "branches": namespaced_branches}))
    return PipelineGraph(
        nodes=nodes,
        edges=[
            edge.model_copy(update={"from_node": f"{prefix}:{edge.from_node}", "to_node": f"{prefix}:{edge.to_node}"})
            for edge in graph.edges
        ],
    )


def _apply_exposed_values(graph: PipelineGraph, values: dict) -> PipelineGraph:
    nodes = []
    for node in graph.nodes:
        params = dict(node.params)
        prefix = f"{node.id}__"
        for key, value in values.items():
            if key.startswith(prefix):
                params[key[len(prefix) :]] = value
        # Handle branch values that might be lists or PipelineGraph
        applied_branches = {}
        for name, branch in node.branches.items():
            if isinstance(branch, list):
                # Convert list to PipelineGraph and apply values
                branch_graph = _coerce_graph({"nodes": branch, "edges": []})
                applied_branches[name] = _apply_exposed_values(branch_graph, values)
            elif isinstance(branch, PipelineGraph):
                applied_branches[name] = _apply_exposed_values(branch, values)
            else:
                applied_branches[name] = branch
        nodes.append(node.model_copy(update={"params": params, "branches": applied_branches}))
    return graph.model_copy(update={"nodes": nodes})


def _expand_graph(graph: PipelineGraph, session: Session, active: list[uuid.UUID] | None = None) -> PipelineGraph:
    active = active or []
    expanded_nodes = []
    expanded_edges = list(graph.edges)
    for original in graph.nodes:
        # Handle branch values that might be lists (legacy format) or PipelineGraph
        # In _expand_graph inside app/services/graph_engine.py:
        expanded_branches = {}
        for name, branch in original.branches.items():
            if isinstance(branch, list):
                branch_graph = _coerce_graph({"nodes": branch, "edges": []})
                expanded_branches[name] = _expand_graph(branch_graph, session, active)
            elif isinstance(branch, PipelineGraph):
                expanded_branches[name] = _expand_graph(branch, session, active)
            elif isinstance(branch, dict):
                branch_graph = _coerce_graph(branch)
                expanded_branches[name] = _expand_graph(branch_graph, session, active)
            else:
                # Fallback or pass-through for primitive branch parameters
                expanded_branches[name] = branch

        node = original.model_copy(update={"branches": expanded_branches})
        macro_id_text = _macro_id(node)
        if not macro_id_text:
            expanded_nodes.append(node)
            continue
        # Skip UUID parsing for macro_input and macro_output nodes
        node_type = _node_type(node)
        if node_type in {"macro_input", "macro_output"}:
            expanded_nodes.append(node)
            continue
        try:
            macro_id = uuid.UUID(macro_id_text)
        except ValueError as exc:
            raise ValueError(f"Node {node.id} has invalid macro id '{macro_id_text}'.") from exc
        if macro_id in active:
            raise GraphCycleError([*(str(item) for item in active), str(macro_id)])
        version = session.exec(
            select(PipelineVersion)
            .where(PipelineVersion.pipeline_id == macro_id)
            .order_by(PipelineVersion.version_number.desc())
            .limit(1)
        ).first()
        if not version:
            raise ValueError(f"Macro pipeline {macro_id} not found.")
        subgraph = _namespace_graph(
            _expand_graph(
                _apply_exposed_values(_coerce_graph(version.pipeline_json), node.params), session, [*active, macro_id]
            ),
            node.id,
        )
        incoming = [edge for edge in expanded_edges if edge.to_node == node.id]
        outgoing = [edge for edge in expanded_edges if edge.from_node == node.id]
        expanded_edges = [edge for edge in expanded_edges if edge.to_node != node.id and edge.from_node != node.id]
        sources = [
            candidate.id
            for candidate in subgraph.nodes
            if not any(edge.to_node == candidate.id for edge in subgraph.edges)
        ]
        sinks = [
            candidate.id
            for candidate in subgraph.nodes
            if not any(edge.from_node == candidate.id for edge in subgraph.edges)
        ]

        # Reconnect incoming edges to primary macro input source (prevents Cartesian product fan-out)
        primary_source = sources[0] if sources else None
        if primary_source:
            for edge in incoming:
                expanded_edges.append(edge.model_copy(update={"to_node": primary_source}))

        # Reconnect outgoing edges from primary macro output sink (prevents Cartesian product fan-out)
        primary_sink = sinks[0] if sinks else None
        if primary_sink:
            for edge in outgoing:
                expanded_edges.append(edge.model_copy(update={"from_node": primary_sink}))

        expanded_edges.extend(subgraph.edges)
        expanded_nodes.extend(subgraph.nodes)
    return PipelineGraph(nodes=expanded_nodes, edges=expanded_edges)


def _validate_graph(graph: PipelineGraph, input_channels: int) -> dict[str, int]:
    graph.validate_no_cycles()
    outputs: dict[str, int] = {}
    nodes = {node.id: node for node in graph.nodes}
    for node_id in topological_sort(graph):
        node = nodes[node_id]
        node_type = _node_type(node)
        incoming = [edge for edge in graph.edges if edge.to_node == node_id]
        ports = {edge.input_port: outputs[edge.from_node] for edge in incoming}
        primary = next(
            (channels for port, channels in ports.items() if port in (None, "image", "input")),
            input_channels if not incoming else next(iter(ports.values())),
        )
        for port, channels in ports.items():
            allowed = OPERATOR_PORT_SPECS.get(node_type, {}).get(port) or OPERATOR_PORT_SPECS.get(node_type, {}).get(
                None
            )
            if allowed and channels not in allowed:
                raise GraphTypeError(
                    f"Type mismatch on node '{node_id}' ({node_type}), port '{port}': "
                    f"expected channels in {allowed}, got {channels} channels."
                )
        if node_type in CONTROL_BRANCHES:
            required = CONTROL_BRANCHES[node_type]
            if set(node.branches) != set(required):
                raise GraphTypeError(f"Control node '{node_id}' requires branches {required}.")
            # Handle branch values that might be lists or PipelineGraph
            branch_outputs = []
            for name in required:
                branch = node.branches.get(name)
                if isinstance(branch, list):
                    # Convert list to PipelineGraph and validate it
                    branch_graph = _coerce_graph({"nodes": branch, "edges": []})
                    branch_outputs.append(_validate_graph(branch_graph, primary))
                elif isinstance(branch, PipelineGraph):
                    branch_outputs.append(_validate_graph(branch, primary))
                else:
                    branch_outputs.append(primary)
            channel_values = [
                next(reversed(result.values()), primary) if result else primary for result in branch_outputs
            ]
            outputs[node_id] = channel_values[0] if node_type == "macro_if_else" else max(channel_values)
        else:
            outputs[node_id] = OPERATOR_OUTPUT_CHANNELS.get(node_type, primary)
    return outputs


def compile_graph(graph: PipelineGraph, session: Session | None = None, input_channels: int = 3) -> list[PipelineStep]:
    expanded = _expand_graph(graph, session) if session is not None else graph
    _validate_graph(expanded, input_channels)
    node_map = {node.id: node for node in expanded.nodes}
    steps = []
    for node_id in topological_sort(expanded):
        node = node_map[node_id]
        node_type = _node_type(node)
        if node_type in {"macro_input", "macro_output"}:
            continue
        compiled_branches = {}
        for name, branch in node.branches.items():
            if isinstance(branch, list):
                branch_graph = _coerce_graph({"nodes": branch, "edges": []})
                compiled_branches[name] = compile_graph(branch_graph, session, input_channels)
            elif isinstance(branch, PipelineGraph):
                compiled_branches[name] = compile_graph(branch, session, input_channels)
            else:
                compiled_branches[name] = branch
        steps.append(PipelineStep(type=node_type, block_id=node.id, params=node.params, branches=compiled_branches))
    return steps


def prepare_pipeline(session: Session, pipeline_id: uuid.UUID, input_channels: int) -> list[PipelineStep]:
    version = session.exec(
        select(PipelineVersion)
        .where(PipelineVersion.pipeline_id == pipeline_id)
        .order_by(PipelineVersion.version_number.desc())
        .limit(1)
    ).first()
    if not version:
        raise ValueError(f"Pipeline {pipeline_id} not found.")
    return compile_graph(_coerce_graph(version.pipeline_json), session, input_channels)


def execute_graph_pipeline(session: Session, pipeline_id: uuid.UUID, request: PipelineRequest) -> PipelineResponse:
    """Compatibility service API: compile here, then delegate the plan to the executor."""
    try:
        image = decode_base64_image(request.image)
        channels = 1 if image.ndim == 2 else image.shape[2]
        request.pipeline = prepare_pipeline(session, pipeline_id, channels)
    except Exception as exc:
        return PipelineResponse(success=False, error=f"Graph preparation error: {exc}", step_results=[])
    from app.services.pipeline_executor import execute_pipeline

    return execute_pipeline(request)


def validate_macro_graph(
    graph: PipelineGraph, session: Session | None = None, macro_id: uuid.UUID | None = None
) -> PipelineGraph:
    graph.validate_no_cycles()
    _expand_graph(graph, session, [macro_id] if macro_id else [])
    return graph
