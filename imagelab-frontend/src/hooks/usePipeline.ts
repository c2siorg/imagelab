import * as Blockly from "blockly";
import type { PipelineGraph } from "../types/macro";
import type { PipelineStep } from "../types/pipeline";
import { extractWorkspaceGraph } from "../utils/extractMacroGraph";

/** Compatibility export: workspace execution now always starts as a graph. */
export function extractExecutableGraph(workspace: Blockly.WorkspaceSvg): PipelineGraph {
  return extractWorkspaceGraph(workspace);
}

/** @deprecated Compatibility adapter for callers that still require flat linear steps. */
export function extractPipeline(workspace: Blockly.WorkspaceSvg): PipelineStep[] {
  const graph = extractWorkspaceGraph(workspace);
  return graph.nodes.map((node) => ({
    block_id: node.id,
    type: node.type ?? node.op ?? "",
    params: node.params ?? {},
  }));
}
