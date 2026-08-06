import * as Blockly from "blockly";
import type { PipelineStep } from "../types/pipeline";
import { expandPipelineMacros } from "../utils/expandPipelineMacros";
import type { PipelineGraph } from "../types/macro";

// Blockly inputTypes.VALUE = 1 (value input connections)
const INPUT_TYPE_VALUE = 1;

export function extractPipeline(workspace: Blockly.WorkspaceSvg): PipelineStep[] {
  const allBlocks = workspace.getTopBlocks(true);
  const readBlock = allBlocks.find((b) => b.type === "basic_readimage");
  if (!readBlock) return [];

  const pipeline: PipelineStep[] = [];
  let block: Blockly.Block | null = readBlock;
  while (block) {
    const params: Record<string, unknown> = {};
    block.inputList.forEach((input) => {
      input.fieldRow.forEach((field) => {
        if (field.name) {
          params[field.name] = field.getValue();
        }
      });
      // Traverse input_value connections (e.g., border blocks plugged into applyborders)
      const connectedBlock = input.connection?.targetBlock();
      if (connectedBlock && (input.type as number) === INPUT_TYPE_VALUE) {
        connectedBlock.inputList.forEach((childInput) => {
          childInput.fieldRow.forEach((field) => {
            if (field.name) {
              params[field.name] = field.getValue();
            }
          });
        });
      }
    });
    pipeline.push({ block_id: block.id, type: block.type, params });
    block = block.getNextBlock();
  }
  return pipeline;
}

/** Extract and unroll macros immediately before an execution request. */
export function extractExecutablePipeline(workspace: Blockly.WorkspaceSvg): PipelineStep[] {
  const pipeline = extractPipeline(workspace);
  const rawGraph: PipelineGraph = {
    nodes: pipeline.map((step) => ({
      id: step.block_id ?? step.type,
      type: step.type,
      params: step.params,
    })),
    edges: pipeline.slice(1).map((step, index) => ({
      from: pipeline[index].block_id ?? pipeline[index].type,
      to: step.block_id ?? step.type,
    })),
  };
  const expandedGraph = expandPipelineMacros(rawGraph, workspace);
  return orderedSteps(expandedGraph);
}

function orderedSteps(graph: PipelineGraph): PipelineStep[] {
  const byId = new Map(graph.nodes.map((node) => [node.id, node]));
  const indegree = new Map(graph.nodes.map((node) => [node.id, 0]));
  const outgoing = new Map<string, string[]>();
  for (const edge of graph.edges) {
    if (!byId.has(edge.from) || !byId.has(edge.to)) continue;
    indegree.set(edge.to, (indegree.get(edge.to) ?? 0) + 1);
    const targets = outgoing.get(edge.from) ?? [];
    targets.push(edge.to);
    outgoing.set(edge.from, targets);
  }

  const queue = graph.nodes.filter((node) => (indegree.get(node.id) ?? 0) === 0);
  const ordered: PipelineStep[] = [];
  while (queue.length > 0) {
    const node = queue.shift();
    if (!node) break;
    ordered.push({
      block_id: node.id,
      type: node.type ?? node.op ?? "",
      params: node.params ?? {},
    });
    for (const target of outgoing.get(node.id) ?? []) {
      const nextIndegree = (indegree.get(target) ?? 1) - 1;
      indegree.set(target, nextIndegree);
      if (nextIndegree === 0) {
        const targetNode = byId.get(target);
        if (targetNode) queue.push(targetNode);
      }
    }
  }

  // Keep a usable execution order even if a malformed graph contains a cycle.
  if (ordered.length !== graph.nodes.length) {
    const emitted = new Set(ordered.map((step) => step.block_id));
    for (const node of graph.nodes) {
      if (!emitted.has(node.id)) {
        ordered.push({
          block_id: node.id,
          type: node.type ?? node.op ?? "",
          params: node.params ?? {},
        });
      }
    }
  }
  return ordered;
}
