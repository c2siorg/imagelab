import * as Blockly from "blockly";
import { FieldColour } from "@blockly/field-colour";

export function setupBlocklyFields() {
  if (!Blockly.registry.getClass(Blockly.registry.Type.FIELD, "field_colour")) {
    Blockly.fieldRegistry.register("field_colour", FieldColour);
  }
}
