import uuid

from sqlmodel import Session, select

from app.models.graph import GraphCycleError, PipelineGraph, topological_sort
from app.models.persistence import PipelineVersion
from app.models.pipeline import PipelineRequest, PipelineResponse, PipelineStep
from app.services.pipeline_executor import execute_pipeline
from app.utils.image import decode_base64_image


class GraphTypeError(ValueError):
    """Exception raised when a port type/channel mismatch is detected in the pipeline graph."""

    pass


# Expected input channels per port for specific operators
# None indicates the default/unnamed port
OPERATOR_PORT_SPECS: dict[str, dict[str | None, list[int]]] = {
    # Conversions
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
    # Blurring / Thresholding
    "thresholding_adaptivethreshold": {"image": [1], None: [1]},
    "thresholding_otsuthreshold": {"image": [1], None: [1]},
    # Custom nodes in tests (e.g. merge / blend)
    "merge_images": {"image": [3, 4], "mask": [1]},
    "blend_images": {"image": [3, 4], "mask": [1]},
}

# Specific channel count outputs for operators
OPERATOR_OUTPUT_CHANNELS: dict[str, int] = {
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


def expand_all_macros(
    graph: PipelineGraph, session: Session, active_macro_ids: list[uuid.UUID] = None
) -> PipelineGraph:
    """
    Recursively expands macro_ref nodes inside the graph by replacing them
    with the corresponding sub-graphs loaded from the database.
    """
    if active_macro_ids is None:
        active_macro_ids = []

    # Find the first macro node
    macro_nodes = [n for n in graph.nodes if n.type == "macro_ref" or n.op == "macro_ref"]
    if not macro_nodes:
        return graph

    node = macro_nodes[0]
    macro_id_str = node.params.get("macro_id")
    if not macro_id_str:
        raise ValueError(f"Node {node.id} is a macro_ref but missing 'macro_id' parameter.")

    macro_id = uuid.UUID(macro_id_str)

    # Check for cyclic macro nesting
    if macro_id in active_macro_ids:
        cycle_path = [str(mid) for mid in active_macro_ids] + [str(macro_id)]
        raise GraphCycleError(cycle_path)

    # Load macro version from DB
    version = session.exec(
        select(PipelineVersion)
        .where(PipelineVersion.pipeline_id == macro_id)
        .order_by(PipelineVersion.version_number.desc())
        .limit(1)
    ).first()
    if not version:
        raise ValueError(f"Macro pipeline {macro_id} not found in database.")

    macro_graph = PipelineGraph.model_validate(version.pipeline_json)

    # Recursively expand the macro graph itself
    expanded_sub = expand_all_macros(macro_graph, session, active_macro_ids + [macro_id])

    # Prefix all nodes in the sub-graph with the macro node's ID
    m_id = node.id
    new_nodes = []
    for sub_node in expanded_sub.nodes:
        new_nodes.append(sub_node.model_copy(update={"id": f"{m_id}:{sub_node.id}"}))

    remaining_nodes = [n for n in graph.nodes if n.id != m_id] + new_nodes

    # Port matching
    sub_inputs = [n.id for n in expanded_sub.nodes if n.type == "macro_input" or n.op == "macro_input"]
    sub_outputs = [n.id for n in expanded_sub.nodes if n.type == "macro_output" or n.op == "macro_output"]

    sub_inputs_sorted = sorted(sub_inputs)
    sub_outputs_sorted = sorted(sub_outputs)
    all_sub_nodes_sorted = sorted([n.id for n in expanded_sub.nodes])

    new_edges = []
    for edge in graph.edges:
        if edge.from_node != m_id and edge.to_node != m_id:
            new_edges.append(edge)
            continue

        # Remap edge entering the macro
        if edge.to_node == m_id:
            target_port = edge.input_port
            if target_port and target_port in all_sub_nodes_sorted:
                target_id = f"{m_id}:{target_port}"
            elif sub_inputs_sorted:
                if target_port and target_port in sub_inputs_sorted:
                    target_id = f"{m_id}:{target_port}"
                else:
                    target_id = f"{m_id}:{sub_inputs_sorted[0]}"
            elif all_sub_nodes_sorted:
                target_id = f"{m_id}:{all_sub_nodes_sorted[0]}"
            else:
                continue
            new_edges.append(edge.model_copy(update={"to_node": target_id}))

        # Remap edge exiting the macro
        if edge.from_node == m_id:
            if sub_outputs_sorted:
                source_id = f"{m_id}:{sub_outputs_sorted[0]}"
            elif all_sub_nodes_sorted:
                source_id = f"{m_id}:{all_sub_nodes_sorted[-1]}"
            else:
                continue
            new_edges.append(edge.model_copy(update={"from_node": source_id}))

    # Add sub-graph edges (prefixed)
    for sub_edge in expanded_sub.edges:
        new_edges.append(
            sub_edge.model_copy(
                update={"from_node": f"{m_id}:{sub_edge.from_node}", "to_node": f"{m_id}:{sub_edge.to_node}"}
            )
        )

    intermediate_graph = PipelineGraph(nodes=remaining_nodes, edges=new_edges)

    # Continue expanding remaining macros
    return expand_all_macros(intermediate_graph, session, active_macro_ids)


def type_integrity_check(graph: PipelineGraph, input_channels: int) -> None:
    """
    Validates port compatibility across the fully expanded graph.
    Raises GraphTypeError if any channel mismatch is detected.
    """
    topo_order = topological_sort(graph)
    node_map = {n.id: n for n in graph.nodes}
    node_output_channels = {}

    for node_id in topo_order:
        node = node_map[node_id]
        node_type = node.type or node.op

        # Find incoming edges to this node
        incoming = [e for e in graph.edges if e.to_node == node_id]

        port_channels = {}
        if not incoming:
            # Source node - receives the input image channels
            primary_channels = input_channels
            port_channels[None] = input_channels
        else:
            primary_channels = None
            for edge in incoming:
                parent_ch = node_output_channels[edge.from_node]
                port_channels[edge.input_port] = parent_ch
                if edge.input_port in (None, "image", "input"):
                    primary_channels = parent_ch

            if primary_channels is None:
                primary_channels = list(port_channels.values())[0]

        # Validate port compatibility
        spec = OPERATOR_PORT_SPECS.get(node_type)
        if spec:
            for port_name, parent_ch in port_channels.items():
                allowed = spec.get(port_name) or spec.get(None)
                if allowed and parent_ch not in allowed:
                    raise GraphTypeError(
                        f"Type mismatch on node '{node_id}' ({node_type}), port '{port_name}': "
                        f"expected channels in {allowed}, got {parent_ch} channels."
                    )

        # Propagate output channels
        out_ch = OPERATOR_OUTPUT_CHANNELS.get(node_type)
        if out_ch is None:
            out_ch = primary_channels

        node_output_channels[node_id] = out_ch


def prepare_pipeline(session: Session, pipeline_id: uuid.UUID, input_channels: int) -> list[PipelineStep]:
    """
    Loads, expands, cycle-checks, topo-sorts, type-checks a pipeline graph,
    and returns the compiled list of PipelineSteps.
    """
    # 1. Load pipeline graph from DB
    version = session.exec(
        select(PipelineVersion)
        .where(PipelineVersion.pipeline_id == pipeline_id)
        .order_by(PipelineVersion.version_number.desc())
        .limit(1)
    ).first()
    if not version:
        raise ValueError(f"Pipeline {pipeline_id} not found in database.")

    graph = PipelineGraph.model_validate(version.pipeline_json)

    # 2. Recursively expand macros
    expanded_graph = expand_all_macros(graph, session)

    # 3. Run cycle check on the fully expanded graph
    expanded_graph.validate_no_cycles()

    # 4. Run type-integrity check
    type_integrity_check(expanded_graph, input_channels)

    # 5. Run topo sort to compile execution order
    topo_order = topological_sort(expanded_graph)

    # 6. Map sorted nodes to flat PipelineSteps
    node_map = {n.id: n for n in expanded_graph.nodes}
    steps = []
    for node_id in topo_order:
        node = node_map[node_id]
        # Skip macro placeholders or input/output portal nodes during execution
        if node.type in ("macro_input", "macro_output") or node.op in ("macro_input", "macro_output"):
            continue
        steps.append(PipelineStep(type=node.type or node.op or "", block_id=node.id, params=node.params))

    return steps


def execute_graph_pipeline(session: Session, pipeline_id: uuid.UUID, request: PipelineRequest) -> PipelineResponse:
    """
    Executes a pipeline graph by compiling it to flat steps and delegating
    to the sequential PipelineExecutor.
    """
    # Determine channel count from request image
    try:
        image = decode_base64_image(request.image)
        input_channels = 1 if image.ndim == 2 else image.shape[2]
    except Exception as e:
        return PipelineResponse(
            success=False,
            error=f"Failed to decode image: {e}",
            step_results=[],
        )

    # Compile DAG to flat steps list
    try:
        steps = prepare_pipeline(session, pipeline_id, input_channels)
    except GraphCycleError as e:
        return PipelineResponse(
            success=False,
            error=str(e),
            step_results=[],
        )
    except GraphTypeError as e:
        return PipelineResponse(
            success=False,
            error=str(e),
            step_results=[],
        )
    except Exception as e:
        return PipelineResponse(
            success=False,
            error=f"Graph preparation error: {e}",
            step_results=[],
        )

    # Inject steps into request and execute using PipelineExecutor
    request.pipeline = steps
    return execute_pipeline(request)


def validate_macro_graph(graph: PipelineGraph, session: Session, macro_id: uuid.UUID | None = None) -> PipelineGraph:
    """
    Validates a macro graph for structure correctness, cycle detection, and cyclic nesting.
    """
    graph.validate_no_cycles()
    active_macro_ids = [macro_id] if macro_id else []
    expand_all_macros(graph, session, active_macro_ids=active_macro_ids)
    return graph


def expand_macro_steps(steps: list[PipelineStep], session: Session) -> list[PipelineStep]:
    """
    Recursively unrolls any macro_ref, macro_blend, or macro_if_else steps in a list of PipelineSteps.
    """
    from app.services.pipeline_executor import expand_macro_steps as _expand_macro_steps

    return _expand_macro_steps(steps, session=session)
