// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "detection_blobdetection";

const EXPECTED_DEFAULTS: Record<string, string | number | boolean> = {
  min_threshold: 10,
  max_threshold: 200,
  filter_by_area: true,
  min_area: 20,
  max_area: 50000,
  filter_by_circularity: false,
  min_circularity: 0.7,
  filter_by_convexity: false,
  min_convexity: 0.8,
  filter_by_inertia: false,
  min_inertia_ratio: 0.1,
  rgbcolors_input: "#00ffff",
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

describe("detection_blobdetection block", () => {
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

      block.setFieldValue(-10, "min_threshold");
      expect(block.getFieldValue("min_threshold")).toBe(0);

      block.setFieldValue(300, "min_threshold");
      expect(block.getFieldValue("min_threshold")).toBe(254);

      block.setFieldValue(0, "max_threshold");
      expect(block.getFieldValue("max_threshold")).toBe(1);

      block.setFieldValue(500, "max_threshold");
      expect(block.getFieldValue("max_threshold")).toBe(255);

      block.setFieldValue(-5, "min_area");
      expect(block.getFieldValue("min_area")).toBe(1);

      block.setFieldValue(200000, "max_area");
      expect(block.getFieldValue("max_area")).toBe(100000);

      block.setFieldValue(0.001, "min_circularity");
      expect(block.getFieldValue("min_circularity")).toBe(0.01);

      block.setFieldValue(2.0, "min_circularity");
      expect(block.getFieldValue("min_circularity")).toBe(1.0);
    });
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);

      block.setFieldValue(15, "min_threshold");
      block.setFieldValue(220, "max_threshold");
      block.setFieldValue("TRUE", "filter_by_area");
      block.setFieldValue(50, "min_area");
      block.setFieldValue(1500, "max_area");
      block.setFieldValue("TRUE", "filter_by_circularity");
      block.setFieldValue(0.6, "min_circularity");
      block.setFieldValue("FALSE", "filter_by_convexity");
      block.setFieldValue(0.85, "min_convexity");
      block.setFieldValue("FALSE", "filter_by_inertia");
      block.setFieldValue(0.2, "min_inertia_ratio");
      block.setFieldValue("#ff0000", "rgbcolors_input");

      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        min_threshold: 15,
        max_threshold: 220,
        filter_by_area: "TRUE",
        min_area: 50,
        max_area: 1500,
        filter_by_circularity: "TRUE",
        min_circularity: 0.6,
        filter_by_convexity: "FALSE",
        min_convexity: 0.85,
        filter_by_inertia: "FALSE",
        min_inertia_ratio: 0.2,
        rgbcolors_input: "#ff0000",
      });
    });
  });

  it("is registered under the Detection category in the sidebar", () => {
    const detection = categories.find((c) => c.name === "Detection");
    expect(detection).toBeDefined();
    const entry = detection?.blocks.find((b) => b.type === BLOCK_TYPE);
    expect(entry).toEqual({
      type: BLOCK_TYPE,
      label: "Simple Blob Detection",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Simple Blob Detection");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(10);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
  });
});
