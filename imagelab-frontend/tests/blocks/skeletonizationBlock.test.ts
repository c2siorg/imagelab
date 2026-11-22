// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "transformation_skeletonization";

const EXPECTED_DEFAULTS: Record<string, string | number | boolean> = {
  element: "CROSS",
  kernel_size: "3",
  threshold: 127,
  invert: false,
  max_iterations: 0,
  output_mode: "BINARY_MASK",
  skeleton_color: "#00ffff",
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

describe("transformation_skeletonization block", () => {
  it("is defined with the backend params and their defaults", () => {
    withWorkspace((ws) => {
      const block = ws.newBlock(BLOCK_TYPE);
      for (const [name, value] of Object.entries(EXPECTED_DEFAULTS)) {
        if (typeof value === "boolean") {
          const checkboxVal = block.getFieldValue(name);
          expect(checkboxVal === "TRUE" || checkboxVal === true).toBe(value);
        } else {
          expect(block.getFieldValue(name), name).toBe(value);
        }
      }
    });
  });

  it("clamps numeric fields to the backend's accepted ranges", () => {
    withWorkspace((ws) => {
      const block = ws.newBlock(BLOCK_TYPE);

      block.setFieldValue(-10, "threshold");
      expect(block.getFieldValue("threshold")).toBe(0);

      block.setFieldValue(300, "threshold");
      expect(block.getFieldValue("threshold")).toBe(255);

      block.setFieldValue(-5, "max_iterations");
      expect(block.getFieldValue("max_iterations")).toBe(0);

      block.setFieldValue(999, "max_iterations");
      expect(block.getFieldValue("max_iterations")).toBe(500);
    });
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);

      block.setFieldValue("ELLIPSE", "element");
      block.setFieldValue("5", "kernel_size");
      block.setFieldValue(150, "threshold");
      block.setFieldValue("TRUE", "invert");
      block.setFieldValue(25, "max_iterations");
      block.setFieldValue("OVERLAY", "output_mode");
      block.setFieldValue("#ff00ff", "skeleton_color");

      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        element: "ELLIPSE",
        kernel_size: "5",
        threshold: 150,
        invert: "TRUE",
        max_iterations: 25,
        output_mode: "OVERLAY",
        skeleton_color: "#ff00ff",
      });
    });
  });

  it("is registered under the Transformation category in the sidebar", () => {
    const transformation = categories.find((c) => c.name === "Transformation");
    expect(transformation).toBeDefined();
    const entry = transformation?.blocks.find((b) => b.type === BLOCK_TYPE);
    expect(entry).toEqual({
      type: BLOCK_TYPE,
      label: "Skeletonization",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Morphological Skeletonization");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(7);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
    expect(doc.formula).toBeDefined();
  });
});
