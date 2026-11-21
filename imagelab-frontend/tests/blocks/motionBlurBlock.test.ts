// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "augmentation_motionblur";

const EXPECTED_DEFAULTS: Record<string, number> = {
  kernel_size: 15,
  angle: 0,
};

beforeAll(() => {
  setupBlocklyFields();
  registerAllBlocks();
});

function withWorkspace<T>(fn: (ws: Blockly.Workspace) => T): T {
  const ws = new Blockly.Workspace();
  try {
    return fn(ws);
  } finally {
    ws.dispose();
  }
}

describe("augmentation_motionblur block", () => {
  it("is defined with the backend params and their defaults", () => {
    withWorkspace((ws) => {
      const block = ws.newBlock(BLOCK_TYPE);
      for (const [name, value] of Object.entries(EXPECTED_DEFAULTS)) {
        expect(block.getFieldValue(name), name).toBe(value);
      }
    });
  });

  it("clamps numeric fields to the backend's accepted ranges", () => {
    withWorkspace((ws) => {
      const block = ws.newBlock(BLOCK_TYPE);

      block.setFieldValue(1, "kernel_size");
      expect(block.getFieldValue("kernel_size")).toBe(3);

      block.setFieldValue(100, "kernel_size");
      expect(block.getFieldValue("kernel_size")).toBe(61);

      block.setFieldValue(-10, "angle");
      expect(block.getFieldValue("angle")).toBe(0);

      block.setFieldValue(500, "angle");
      expect(block.getFieldValue("angle")).toBe(360);
    });
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);

      block.setFieldValue(25, "kernel_size");
      block.setFieldValue(45, "angle");

      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        kernel_size: 25,
        angle: 45,
      });
    });
  });

  it("is registered under the Augmentation category in the sidebar", () => {
    const augmentation = categories.find((c) => c.name === "Augmentation");
    expect(augmentation).toBeDefined();
    const entry = augmentation?.blocks.find((b) => b.type === BLOCK_TYPE);
    expect(entry).toEqual({
      type: BLOCK_TYPE,
      label: "Motion Blur",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Motion Blur");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(2);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
  });
});
