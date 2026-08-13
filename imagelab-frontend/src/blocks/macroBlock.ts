import * as Blockly from "blockly";
import type { ExposedParam, MacroDefinition } from "../types/macro";
import { cleanFieldLabel, formatExposedFieldKey } from "../utils/macroFieldKeys";

/**
 * Helper to build the appropriate Blockly field instance based on parameter default value type.
 */
function createFieldForParam(param: ExposedParam): Blockly.Field {
  const val = param.defaultValue;
  if (typeof val === "number") {
    return new Blockly.FieldNumber(val);
  }
  if (typeof val === "boolean") {
    return new Blockly.FieldCheckbox(val ? "TRUE" : "FALSE");
  }
  return new Blockly.FieldTextInput(typeof val === "string" ? val : "");
}

const HEADER_INPUT = "MACRO_HEADER";
const PARAM_INPUT_PREFIX = "MACRO_PARAM_";
type RenderableBlock = Blockly.Block & { render: () => void };

function exposedParamsFor(macro: MacroDefinition): ExposedParam[] {
  return macro.exposedParams ?? macro.graph.exposed_params ?? [];
}

function fieldNameFor(param: ExposedParam): string {
  return formatExposedFieldKey(param.blockId, param.paramName);
}

function labelFor(param: ExposedParam): string {
  const label = param.label || param.paramName;
  return cleanFieldLabel(label);
}

function populateMacroBlock(
  block: Blockly.Block,
  macro: MacroDefinition,
  values = new Map<string, string>(),
): void {
  for (const input of [...block.inputList]) {
    block.removeInput(input.name, true);
  }

  const truncatedName = macro.name.length > 24 ? `${macro.name.slice(0, 22)}\u2026` : macro.name;
  block
    .appendDummyInput(HEADER_INPUT)
    .appendField(new Blockly.FieldLabelSerializable(truncatedName), "MACRO_NAME");

  for (const param of exposedParamsFor(macro)) {
    const fieldName = fieldNameFor(param);
    const field = createFieldForParam(param);
    const savedValue = values.get(fieldName);
    if (savedValue !== undefined) field.setValue(savedValue);
    block
      .appendDummyInput(`${PARAM_INPUT_PREFIX}${fieldName}`)
      .appendField(labelFor(param))
      .appendField(field, fieldName);
  }

  block.setPreviousStatement(true, null);
  block.setNextStatement(true, null);
  block.setColour("#7058a3");
  block.setTooltip(`Macro: ${macro.name}`);
  block.setHelpUrl("");
}

/**
 * Register a saved macro block with vertical stacking for exposed parameters
 * to prevent horizontal block stretching across the canvas.
 */
export function registerMacroBlock(macro: MacroDefinition): void {
  const blockType = `macro_${macro.id}`;

  // Macro definitions are mutable. Replace an old definition so new instances
  // immediately use the latest exposed parameters.
  delete Blockly.Blocks[blockType];

  // Define block using dynamic init function for vertical layout control
  Blockly.Blocks[blockType] = {
    init: function (this: Blockly.Block) {
      populateMacroBlock(this, macro);
    },
  };
}

/** Refresh all placed instances after a macro's exposed parameters change. */
export function refreshMacroBlockInstances(
  workspace: Blockly.WorkspaceSvg | null,
  macro: MacroDefinition,
): void {
  if (!workspace) return;
  for (const block of workspace.getBlocksByType(`macro_${macro.id}`, false)) {
    const values = new Map<string, string>();
    for (const param of exposedParamsFor(macro)) {
      const fieldName = fieldNameFor(param);
      const value = block.getFieldValue(fieldName);
      if (value !== null && value !== undefined) values.set(fieldName, value);
    }
    populateMacroBlock(block, macro, values);
    (block as RenderableBlock).render();
  }
}
