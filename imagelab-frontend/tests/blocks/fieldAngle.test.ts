// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { registerAllBlocks } from "../../src/blocks/definitions";

beforeAll(() => {
  setupBlocklyFields();
  registerAllBlocks();
});

describe("angle field", () => {
  it("registers field_angle", () => {
    expect(Blockly.registry.getClass(Blockly.registry.Type.FIELD, "field_angle")).toBeTruthy();
  });

  it.each(["geometric_rotateimage", "drawingoperations_drawellipse"])(
    "%s has an angle field defaulting to 90",
    (type) => {
      const ws = new Blockly.Workspace();
      const block = ws.newBlock(type);
      expect(block.getField("angle")).not.toBeNull();
      expect(block.getFieldValue("angle")).toBe(90);
      ws.dispose();
    },
  );
});
