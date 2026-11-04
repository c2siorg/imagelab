// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "detection_orb";

const EXPECTED_DEFAULTS: Record<string, string | number | boolean> = {
  nfeatures: 500,
  scaleFactor: 1.2,
  nlevels: 8,
  scoreType: "HARRIS_SCORE",
  fastThreshold: 20,
  drawRichKeypoints: true,
  color: "#00ff00",
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

describe("detection_orb block", () => {
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

  it("clamps numeric fields to the accepted ranges", () => {
    withWorkspace((ws) => {
      const block = ws.newBlock(BLOCK_TYPE);

      block.setFieldValue(5, "nfeatures");
      expect(block.getFieldValue("nfeatures")).toBe(10);
      block.setFieldValue(5000, "nfeatures");
      expect(block.getFieldValue("nfeatures")).toBe(2000);

      block.setFieldValue(1.0, "scaleFactor");
      expect(block.getFieldValue("scaleFactor")).toBe(1.05);
      block.setFieldValue(5.0, "scaleFactor");
      expect(block.getFieldValue("scaleFactor")).toBe(2.0);

      block.setFieldValue(0, "nlevels");
      expect(block.getFieldValue("nlevels")).toBe(1);
      block.setFieldValue(50, "nlevels");
      expect(block.getFieldValue("nlevels")).toBe(16);

      block.setFieldValue(0, "fastThreshold");
      expect(block.getFieldValue("fastThreshold")).toBe(1);
      block.setFieldValue(200, "fastThreshold");
      expect(block.getFieldValue("fastThreshold")).toBe(100);
    });
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);
      block.setFieldValue(150, "nfeatures");
      block.setFieldValue(1.4, "scaleFactor");
      block.setFieldValue(4, "nlevels");
      block.setFieldValue("FAST_SCORE", "scoreType");
      block.setFieldValue(30, "fastThreshold");
      block.setFieldValue("FALSE", "drawRichKeypoints");
      block.setFieldValue("#ff0000", "color");
      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        nfeatures: 150,
        scaleFactor: 1.4,
        nlevels: 4,
        scoreType: "FAST_SCORE",
        fastThreshold: 30,
        drawRichKeypoints: "FALSE",
        color: "#ff0000",
      });
    });
  });

  it("is registered under the Detection category in the sidebar", () => {
    const detection = categories.find((c) => c.name === "Detection");
    expect(detection).toBeDefined();
    const entry = detection?.blocks.find((b) => b.type === BLOCK_TYPE);
    expect(entry).toEqual({
      type: BLOCK_TYPE,
      label: "ORB Feature Detection",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("ORB Feature Detection");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(6);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
  });
});
