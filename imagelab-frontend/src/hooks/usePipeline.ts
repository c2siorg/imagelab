import * as Blockly from "blockly";
import type { PipelineStep } from "../types/pipeline";

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
    pipeline.push({ type: block.type, params });
    block = block.getNextBlock();
  }
  return pipeline;
}
