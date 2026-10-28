// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";

const BLOCK_TYPE = "thresholding_inrange";

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

describe("thresholding_inrange block", () => {
  it("initializes default parameter values and output mode", () => {
    withBlock((block) => {
      expect(block.getFieldValue("lower1")).toBe(0);
      expect(block.getFieldValue("upper1")).toBe(255);
      expect(block.getFieldValue("lower2")).toBe(0);
      expect(block.getFieldValue("upper2")).toBe(255);
      expect(block.getFieldValue("lower3")).toBe(0);
      expect(block.getFieldValue("upper3")).toBe(255);
      expect(block.getFieldValue("outputMode")).toBe("mask");
    });
  });

  it("clamps channel bounds to the [0, 255] range", () => {
    withBlock((block) => {
      block.setFieldValue(-10, "lower1");
      expect(block.getFieldValue("lower1")).toBe(0);
      block.setFieldValue(300, "upper1");
      expect(block.getFieldValue("upper1")).toBe(255);
    });
  });

  it("allows switching output mode to masked_image", () => {
    withBlock((block) => {
      block.setFieldValue("masked_image", "outputMode");
      expect(block.getFieldValue("outputMode")).toBe("masked_image");
    });
  });

  it("is registered in the Thresholding category and documented in operatorDocs", () => {
    const thresholding = categories.find((category) => category.name === "Thresholding");
    expect(thresholding?.blocks.map((block) => block.type)).toContain(BLOCK_TYPE);
    expect(operatorDocs[BLOCK_TYPE]?.name).toBe("In-Range Color Mask");
    expect(operatorDocs[BLOCK_TYPE]?.parameters.length).toBeGreaterThan(0);
  });
});
