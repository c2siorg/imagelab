import * as Blockly from "blockly";
import type { ExposedParam, MacroDefinition } from "../types/macro";

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

/**
 * Register a saved macro block with vertical stacking for exposed parameters
 * to prevent horizontal block stretching across the canvas.
 */
export function registerMacroBlock(macro: MacroDefinition): void {
  const blockType = `macro_${macro.id}`;

  // Avoid re-registering an already defined block
  if (blockType in Blockly.Blocks) return;

  const truncatedName = macro.name.length > 24 ? `${macro.name.slice(0, 22)}\u2026` : macro.name;
  const exposedParams = macro.exposedParams ?? macro.graph.exposed_params ?? [];

  // Define block using dynamic init function for vertical layout control
  Blockly.Blocks[blockType] = {
    init: function (this: Blockly.Block) {
      // 1. Header row (Macro Title)
      this.appendDummyInput().appendField(
        new Blockly.FieldLabelSerializable(truncatedName),
        "MACRO_NAME",
      );

      // 2. Add each exposed parameter on its own new row
      for (const param of exposedParams) {
        const fieldName = `${param.blockId}__${param.paramName}`;
        const labelText = param.label ?? param.paramName;
        const field = createFieldForParam(param);

        this.appendDummyInput().appendField(labelText).appendField(field, fieldName);
      }

      // 3. Connectors & Styling
      this.setPreviousStatement(true, null);
      this.setNextStatement(true, null);
      this.setColour("#7058a3");
      this.setTooltip(`Macro: ${macro.name}`);
      this.setHelpUrl("");
    },
  };
}
