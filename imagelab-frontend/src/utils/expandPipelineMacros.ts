import * as Blockly from "blockly";
import { useMacroStore } from "../store/useMacroStore";
import type { ExposedParam, GraphEdge, GraphNode, PipelineGraph } from "../types/macro";

const MAX_DEPTH = 10;

type NormalizedGraphNode = GraphNode & {
  params: Record<string, unknown>;
};

function isMacroNode(node: GraphNode): boolean {
  return (node.type ?? node.op ?? "").startsWith("macro_");
}

function macroIdFor(node: GraphNode): string {
  return (node.type ?? node.op ?? "").replace(/^macro_/, "");
}

function cloneNode(node: GraphNode, wrapperId: string): NormalizedGraphNode {
  return {
    ...node,
    id: `${wrapperId}:${node.id}`,
    params: node.params ? { ...node.params } : {},
  };
}

function cloneEdge(edge: GraphEdge, wrapperId: string): GraphEdge {
  return {
    ...edge,
    from: `${wrapperId}:${edge.from}`,
    to: `${wrapperId}:${edge.to}`,
  };
}

function valueForExposedParam(macroBlock: Blockly.Block | null, param: ExposedParam): unknown {
  const value = macroBlock?.getFieldValue(`${param.blockId}__${param.paramName}`);
  if (value === undefined || value === null) return param.defaultValue;
  if (typeof param.defaultValue === "number") {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? param.defaultValue : parsed;
  }
  if (typeof param.defaultValue === "boolean") return value === "TRUE" || value === "true";
  return value;
}

/**
 * Replaces macro wrapper nodes with their saved internal graph. Internal ids
 * are namespaced by the wrapper id so multiple instances stay independent.
 */
export function expandPipelineMacros(
  graph: PipelineGraph,
  workspace: Blockly.WorkspaceSvg | null,
): PipelineGraph {
  const macros = useMacroStore.getState().macros;
  let nodes: NormalizedGraphNode[] = graph.nodes.map((node) => ({
    ...node,
    params: node.params ? { ...node.params } : {},
  }));
  let edges: GraphEdge[] = graph.edges.map((edge) => ({ ...edge }));

  const pending: NormalizedGraphNode[] = [...nodes];
  const visitedNodeIds = new Set<string>();

  while (pending.length > 0) {
    const wrapper = pending.shift();
    if (!wrapper) break;

    // Check current expansion depth by counting colons in the node ID
    const currentDepth = (wrapper.id.match(/:/g) || []).length;
    if (currentDepth >= MAX_DEPTH) {
      throw new Error(
        `Macro expansion depth exceeded maximum of ${MAX_DEPTH}. Possible circular reference.`,
      );
    }

    // Prevent processing the same node multiple times (prevents infinite loops)
    if (visitedNodeIds.has(wrapper.id)) {
      continue;
    }
    visitedNodeIds.add(wrapper.id);

    if (!isMacroNode(wrapper)) continue;

    const macroId = macroIdFor(wrapper);
    const macro = macros.find((candidate) => candidate.id === macroId);
    if (!macro) continue;

    const incoming = edges.filter((edge) => edge.to === wrapper.id);
    const outgoing = edges.filter((edge) => edge.from === wrapper.id);

    // 1. Guard against empty macro graphs
    if (!macro.graph?.nodes || macro.graph.nodes.length === 0) {
      // Bypass empty macro: bridge incoming edges directly to outgoing edges
      for (const inEdge of incoming) {
        for (const outEdge of outgoing) {
          edges.push({ ...inEdge, to: outEdge.to, input_port: outEdge.input_port });
        }
      }
      nodes = nodes.filter((node) => node.id !== wrapper.id);
      edges = edges.filter((edge) => edge.from !== wrapper.id && edge.to !== wrapper.id);
      continue;
    }

    // 2. Clone internal nodes and edges with wrapper namespacing
    const internalNodes: NormalizedGraphNode[] = macro.graph.nodes.map((node) =>
      cloneNode(node, wrapper.id),
    );
    const internalEdges: GraphEdge[] = macro.graph.edges.map((edge) => cloneEdge(edge, wrapper.id));
    const macroBlock = workspace?.getBlockById(wrapper.id) ?? null;

    // 3. Inject exposed workspace parameter values into internal target nodes
    const exposedParams = macro.exposedParams ?? macro.graph.exposed_params ?? [];
    for (const param of exposedParams) {
      const target = internalNodes.find(
        (innerNode) => innerNode.id === `${wrapper.id}:${param.blockId}`,
      );
      if (target) {
        target.params = {
          ...target.params,
          [param.paramName]: valueForExposedParam(macroBlock, param),
        };
      }
    }

    // 4. Identify internal sources (entry points) & sinks (exit points)
    const sources = internalNodes.filter(
      (node) => !internalEdges.some((edge) => edge.to === node.id),
    );
    const sinks = internalNodes.filter(
      (node) => !internalEdges.some((edge) => edge.from === node.id),
    );

    // 5. Replace wrapper node with internal nodes & edges in pipeline graph
    nodes = nodes.filter((node) => node.id !== wrapper.id).concat(internalNodes);
    edges = edges
      .filter((edge) => edge.from !== wrapper.id && edge.to !== wrapper.id)
      .concat(internalEdges);

    // Push new internal nodes to pending queue in case of nested macros
    pending.push(...internalNodes);

    // 6. Connect boundary edges to internal sources & sinks
    for (const edge of incoming) {
      for (const source of sources) {
        edges.push({ ...edge, to: source.id });
      }
    }
    for (const edge of outgoing) {
      for (const sink of sinks) {
        edges.push({ ...edge, from: sink.id });
      }
    }
  }

  return { ...graph, nodes, edges };
}
