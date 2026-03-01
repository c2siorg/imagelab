import * as Blockly from "blockly";
import { registerReadImageExtension } from "../extensions/readImageExtension";
import { basicBlocks } from "./basic.blocks";
import { geometricBlocks } from "./geometric.blocks";
import { conversionsBlocks } from "./conversions.blocks";
import { drawingBlocks } from "./drawing.blocks";
import { blurringBlocks } from "./blurring.blocks";
import { filteringBlocks } from "./filtering.blocks";
import { thresholdingBlocks } from "./thresholding.blocks";
import { sobelDerivativesBlocks } from "./sobel-derivatives.blocks";
import { transformationBlocks } from "./transformation.blocks";
import { segmentationBlocks } from "./segmentation.blocks";

function registerOddKernelValidator() {
  if (Blockly.Extensions.isRegistered("odd_kernel_validator")) return;

  Blockly.Extensions.register("odd_kernel_validator", function (this: Blockly.Block) {
    const field = this.getField("kernelSize");
    if (!field) {
      console.warn(
        `[odd_kernel_validator] Field "kernelSize" not found on block type "${this.type}". Validator not applied.`,
      );
      return;
    }

    field.setValidator((newValue: number): number | null => {
      if (!Number.isFinite(newValue)) return null;

      let normalized = Math.max(1, Math.round(newValue));
      if (normalized % 2 === 0) normalized += 1;
      return normalized;
    });
  });
}

export function registerAllBlocks() {
  registerReadImageExtension();
  registerOddKernelValidator();
  Blockly.defineBlocksWithJsonArray([
    ...basicBlocks,
    ...geometricBlocks,
    ...conversionsBlocks,
    ...drawingBlocks,
    ...blurringBlocks,
    ...filteringBlocks,
    ...thresholdingBlocks,
    ...sobelDerivativesBlocks,
    ...transformationBlocks,
    ...segmentationBlocks,
  ]);
}
