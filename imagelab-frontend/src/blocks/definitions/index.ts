import * as Blockly from 'blockly';
import { registerReadImageExtension } from '../extensions/readImageExtension';
import { basicBlocks } from './basic.blocks';
import { geometricBlocks } from './geometric.blocks';
import { conversionsBlocks } from './conversions.blocks';
import { drawingBlocks } from './drawing.blocks';
import { blurringBlocks } from './blurring.blocks';
import { filteringBlocks } from './filtering.blocks';
import { thresholdingBlocks } from './thresholding.blocks';
import { sobelDerivativesBlocks } from './sobel-derivatives.blocks';
import { transformationBlocks } from './transformation.blocks';

export function registerAllBlocks() {
  registerReadImageExtension();

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
  ]);
}
