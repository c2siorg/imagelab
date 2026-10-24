// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";

const BLOCK_TYPE = "imageconversions_gammacorrection";

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

describe("imageconversions_gammacorrection block", () => {
  it("defaults gamma to 1.0", () => {
    withBlock((block) => expect(block.getFieldValue("gamma")).toBe(1));
  });

  it("clamps gamma to the range the backend accepts", () => {
    withBlock((block) => {
      block.setFieldValue(0, "gamma");
      expect(block.getFieldValue("gamma")).toBe(0.1);
      block.setFieldValue(9, "gamma");
      expect(block.getFieldValue("gamma")).toBe(5);
    });
  });

  it("is listed in the Conversions category and documented", () => {
    const conversions = categories.find((category) => category.name === "Conversions");
    expect(conversions?.blocks.map((block) => block.type)).toContain(BLOCK_TYPE);
    expect(operatorDocs[BLOCK_TYPE]?.name).toBe("Gamma Correction");
  });
});
