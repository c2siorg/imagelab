import * as Blockly from "blockly";
import { registerFieldAngle } from "@blockly/field-angle";
import { FieldColour } from "@blockly/field-colour";

/** Blockly icons, cursors and sounds, copied from node_modules/blockly/media/ into public/. */
export const BLOCKLY_MEDIA_PATH = "/blockly-media/";

export function setupBlocklyFields() {
  if (!Blockly.registry.hasItem(Blockly.registry.Type.FIELD, "field_colour")) {
    Blockly.fieldRegistry.register("field_colour", FieldColour);
  }
  // @blockly/field-angle v6+ no longer registers itself on import.
  if (!Blockly.registry.hasItem(Blockly.registry.Type.FIELD, "field_angle")) {
    registerFieldAngle();
  }
}
