// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";

const BLOCK_TYPE = "imageconversions_bitplaneslicing";

beforeAll(() => {
  setupBlocklyFields();
  registerAllBlocks();
});

function withBlock<T>(fn: (block: Blockly.Block) => T): T {
  const ws = new Blockly.Workspace();
  try {
    return fn(ws.newBlock(BLOCK_TYPE));
  } finally {
    ws.dispose();
  }
}

describe("imageconversions_bitplaneslicing block", () => {
  it("defaults to the most significant bit", () => {
    withBlock((block) => {
      expect(block.getFieldValue("bit")).toBe(7);
    });
  });

  it("clamps the bit to the [0, 7] range", () => {
    withBlock((block) => {
      block.setFieldValue(-3, "bit");
      expect(block.getFieldValue("bit")).toBe(0);
      block.setFieldValue(12, "bit");
      expect(block.getFieldValue("bit")).toBe(7);
    });
  });

  it("only accepts whole numbers", () => {
    withBlock((block) => {
      block.setFieldValue(3.6, "bit");
      expect(block.getFieldValue("bit")).toBe(4);
    });
  });

  it("is registered in the Conversions category and documented in operatorDocs", () => {
    const conversions = categories.find((category) => category.name === "Conversions");
    expect(conversions?.blocks.map((block) => block.type)).toContain(BLOCK_TYPE);
    expect(operatorDocs[BLOCK_TYPE]?.name).toBe("Bit-Plane Slicing");
    expect(operatorDocs[BLOCK_TYPE]?.parameters.length).toBeGreaterThan(0);
  });
});
