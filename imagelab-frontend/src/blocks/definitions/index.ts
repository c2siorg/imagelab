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

export function registerAllBlocks() {
  registerReadImageExtension();

  // Registered odd kernel validator before defining blocks
  Blockly.Extensions.register("odd_kernel_validator", function () {
    const field = this.getField("kernelSize");

    if (!field) return;

    field.setValidator(function (newValue: string) {
      let value = parseInt(newValue, 10);

      if (isNaN(value) || value <= 0) return 5; // Default to 5 if invalid

      // Force odd number
      if (value % 2 === 0) {
        value += 1;
      }

      return value;
    });
  });

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
