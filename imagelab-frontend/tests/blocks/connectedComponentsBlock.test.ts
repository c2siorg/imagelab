// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "segmentation_connectedcomponents";

// Field names must match the keys the backend operator reads from params.
const EXPECTED_DEFAULTS: Record<string, string | number | boolean> = {
  connectivity: "8",
  invert: false,
  min_area: 50,
  output_mode: "COLOR_MAP",
  rgbcolors_input: "#00ffff",
  thickness: 2,
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

describe("segmentation_connectedcomponents block", () => {
  it("is defined with the backend params and their defaults", () => {
    withWorkspace((ws) => {
      const block = ws.newBlock(BLOCK_TYPE);
      for (const [name, value] of Object.entries(EXPECTED_DEFAULTS)) {
        if (typeof value === "boolean") {
          const val = block.getFieldValue(name);
          expect(val === "TRUE" || val === true).toBe(value);
        } else {
          expect(block.getFieldValue(name), name).toBe(value);
        }
      }
    });
  });

  it("clamps numeric fields to the backend's accepted ranges", () => {
    withWorkspace((ws) => {
      const block = ws.newBlock(BLOCK_TYPE);

      block.setFieldValue(-10, "min_area");
      expect(block.getFieldValue("min_area")).toBe(0);

      block.setFieldValue(200000, "min_area");
      expect(block.getFieldValue("min_area")).toBe(100000);

      block.setFieldValue(0, "thickness");
      expect(block.getFieldValue("thickness")).toBe(1);

      block.setFieldValue(50, "thickness");
      expect(block.getFieldValue("thickness")).toBe(20);
    });
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);
      block.setFieldValue("4", "connectivity");
      block.setFieldValue("TRUE", "invert");
      block.setFieldValue(120, "min_area");
      block.setFieldValue("BOUNDING_BOX", "output_mode");
      block.setFieldValue("#ff0000", "rgbcolors_input");
      block.setFieldValue(4, "thickness");
      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        connectivity: "4",
        invert: "TRUE",
        min_area: 120,
        output_mode: "BOUNDING_BOX",
        rgbcolors_input: "#ff0000",
        thickness: 4,
      });
    });
  });

  it("is registered under the Segmentation category in the sidebar", () => {
    const segmentation = categories.find((c) => c.name === "Segmentation");
    expect(segmentation).toBeDefined();
    const entry = segmentation?.blocks.find((b) => b.type === BLOCK_TYPE);
    expect(entry).toEqual({
      type: BLOCK_TYPE,
      label: "Connected Components",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Connected Components");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(5);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
  });
});
