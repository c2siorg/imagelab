// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "augmentation_cutout";

const EXPECTED_DEFAULTS: Record<string, string | number | boolean> = {
  num_holes: 1,
  hole_size: 32,
  fill_mode: "CONSTANT",
  fill_color: "#000000",
  seed: 0,
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

describe("augmentation_cutout block", () => {
  it("is defined with the backend params and their defaults", () => {
    withWorkspace((ws) => {
      const block = ws.newBlock(BLOCK_TYPE);
      for (const [name, value] of Object.entries(EXPECTED_DEFAULTS)) {
        expect(block.getFieldValue(name), name).toBe(value);
      }
    });
  });

  it("clamps numeric fields to the accepted ranges", () => {
    withWorkspace((ws) => {
      const block = ws.newBlock(BLOCK_TYPE);

      block.setFieldValue(-5, "num_holes");
      expect(block.getFieldValue("num_holes")).toBe(1);

      block.setFieldValue(50, "num_holes");
      expect(block.getFieldValue("num_holes")).toBe(20);

      block.setFieldValue(1, "hole_size");
      expect(block.getFieldValue("hole_size")).toBe(4);

      block.setFieldValue(1000, "hole_size");
      expect(block.getFieldValue("hole_size")).toBe(512);

      block.setFieldValue(-10, "seed");
      expect(block.getFieldValue("seed")).toBe(0);
    });
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);

      block.setFieldValue(4, "num_holes");
      block.setFieldValue(48, "hole_size");
      block.setFieldValue("RANDOM_NOISE", "fill_mode");
      block.setFieldValue("#123456", "fill_color");
      block.setFieldValue(42, "seed");

      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        num_holes: 4,
        hole_size: 48,
        fill_mode: "RANDOM_NOISE",
        fill_color: "#123456",
        seed: 42,
      });
    });
  });

  it("is registered under the Augmentation category in the sidebar", () => {
    const augmentation = categories.find((c) => c.name === "Augmentation");
    expect(augmentation).toBeDefined();
    const entry = augmentation?.blocks.find((b) => b.type === BLOCK_TYPE);
    expect(entry).toEqual({
      type: BLOCK_TYPE,
      label: "Cutout",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Cutout Augmentation");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(5);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
    expect(doc.formula).toBeDefined();
  });
});
