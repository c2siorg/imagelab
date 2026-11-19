// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "augmentation_vignette";

const EXPECTED_DEFAULTS: Record<string, string | number | boolean> = {
  radius: 0.8,
  intensity: 0.6,
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

describe("augmentation_vignette block", () => {
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

      block.setFieldValue(-0.5, "radius");
      expect(block.getFieldValue("radius")).toBe(0.1);

      block.setFieldValue(5.0, "radius");
      expect(block.getFieldValue("radius")).toBe(2.0);

      block.setFieldValue(-1.0, "intensity");
      expect(block.getFieldValue("intensity")).toBe(0);

      block.setFieldValue(2.5, "intensity");
      expect(block.getFieldValue("intensity")).toBe(1);
    });
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);

      block.setFieldValue(1.2, "radius");
      block.setFieldValue(0.35, "intensity");

      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        radius: 1.2,
        intensity: 0.35,
      });
    });
  });

  it("is registered under the Augmentation category in the sidebar", () => {
    const augmentation = categories.find((c) => c.name === "Augmentation");
    expect(augmentation).toBeDefined();
    const entry = augmentation?.blocks.find((b) => b.type === BLOCK_TYPE);
    expect(entry).toEqual({
      type: BLOCK_TYPE,
      label: "Vignette Filter",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Vignette Filter");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(2);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
  });
});
