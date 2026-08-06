import * as Blockly from "blockly";
import { useMacroStore } from "../store/useMacroStore";
import type { ExposedParam, GraphEdge, GraphNode, PipelineGraph } from "../types/macro";

function isMacroNode(node: GraphNode): boolean {
  return (node.type ?? node.op ?? "").startsWith("macro_");
}

function macroIdFor(node: GraphNode): string {
  return (node.type ?? node.op ?? "").replace(/^macro_/, "");
}

function cloneNode(node: GraphNode, wrapperId: string): GraphNode {
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
 * Replaces macro wrapper nodes with their saved internal graph.  Internal ids
 * are namespaced by the wrapper id so multiple instances stay independent.
 */
export function expandPipelineMacros(
  graph: PipelineGraph,
  workspace: Blockly.WorkspaceSvg | null,
): PipelineGraph {
  const macros = useMacroStore.getState().macros;
  let nodes = graph.nodes.map((node) => ({
    ...node,
    params: node.params ? { ...node.params } : {},
  }));
  let edges = graph.edges.map((edge) => ({ ...edge }));

  const pending = [...nodes];
  while (pending.length > 0) {
    const wrapper = pending.shift();
    if (!wrapper) break;
    if (!isMacroNode(wrapper)) continue;
    const macro = macros.find((candidate) => candidate.id === macroIdFor(wrapper));
    if (!macro) continue;

    const internalNodes = macro.graph.nodes.map((node) => cloneNode(node, wrapper.id));
    const internalEdges = macro.graph.edges.map((edge) => cloneEdge(edge, wrapper.id));
    const macroBlock = workspace?.getBlockById(wrapper.id) ?? null;

    for (const param of macro.exposedParams ?? macro.graph.exposed_params ?? []) {
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

    const internalIds = new Set(macro.graph.nodes.map((node) => node.id));
    const sources = macro.graph.nodes.filter(
      (node) => !macro.graph.edges.some((edge) => edge.to === node.id),
    );
    const sinks = macro.graph.nodes.filter(
      (node) => !macro.graph.edges.some((edge) => edge.from === node.id),
    );
    const incoming = edges.filter((edge) => edge.to === wrapper.id);
    const outgoing = edges.filter((edge) => edge.from === wrapper.id);

    nodes = nodes.filter((node) => node.id !== wrapper.id).concat(internalNodes);
    edges = edges
      .filter((edge) => edge.from !== wrapper.id && edge.to !== wrapper.id)
      .concat(internalEdges);
    pending.push(...internalNodes);

    // Preserve the wrapper's surrounding graph connections at the macro's boundary.
    for (const edge of incoming) {
      for (const source of sources) {
        edges.push({ ...edge, to: `${wrapper.id}:${source.id}` });
      }
    }
    for (const edge of outgoing) {
      for (const sink of sinks) {
        edges.push({ ...edge, from: `${wrapper.id}:${sink.id}` });
      }
    }

    // Empty macro graphs have no executable replacement; do not leave dangling edges.
    if (internalIds.size === 0) continue;
  }

  return { ...graph, nodes, edges };
}
