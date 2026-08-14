import * as Blockly from "blockly";
import type { PipelineStep } from "../types/pipeline";
import { expandPipelineMacros } from "../utils/expandPipelineMacros";
import type { PipelineGraph } from "../types/macro";

const INPUT_TYPE_VALUE = 1;
const INPUT_TYPE_STATEMENT = 3;

function extractStepChain(startBlock: Blockly.Block | null): PipelineStep[] {
  const chain: PipelineStep[] = [];
  let curr = startBlock;
  while (curr) {
    const params: Record<string, unknown> = {};
    if (Array.isArray(curr.inputList)) {
      curr.inputList.forEach((input) => {
        input.fieldRow.forEach((field) => {
          if (field.name) {
            params[field.name] = field.getValue();
          }
        });
        const connectedBlock = input.connection?.targetBlock
          ? input.connection.targetBlock()
          : null;
        if (connectedBlock && (input.type as number) === INPUT_TYPE_VALUE) {
          connectedBlock.inputList.forEach((childInput) => {
            childInput.fieldRow.forEach((field) => {
              if (field.name) {
                params[field.name] = field.getValue();
              }
            });
          });
        } else if (connectedBlock && (input.type as number) === INPUT_TYPE_STATEMENT) {
          const subChain = extractStepChain(connectedBlock);
          if (input.name === "OP1") params["op1_branch"] = subChain;
          else if (input.name === "OP2") params["op2_branch"] = subChain;
          else if (input.name === "IF_BRANCH") params["if_branch"] = subChain;
          else if (input.name === "ELSE_BRANCH") params["else_branch"] = subChain;
          else params[input.name.toLowerCase()] = subChain;
        }
      });
    }
    chain.push({ block_id: curr.id, type: curr.type, params });
    curr = typeof curr.getNextBlock === "function" ? curr.getNextBlock() : null;
  }
  return chain;
}

export function extractPipeline(workspace: Blockly.WorkspaceSvg): PipelineStep[] {
  const allBlocks = workspace.getTopBlocks(true);
  const readBlock = allBlocks.find((b) => b.type === "basic_readimage");
  if (!readBlock) return [];

  return extractStepChain(readBlock);
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
