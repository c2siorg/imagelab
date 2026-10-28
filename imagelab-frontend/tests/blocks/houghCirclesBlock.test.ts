// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "filtering_houghcircles";

// Field names must match the keys the backend operator reads from params.
const EXPECTED_DEFAULTS: Record<string, string | number | boolean> = {
  dp: 1.2,
  minDist: 20,
  param1: 100,
  param2: 30,
  minRadius: 0,
  maxRadius: 0,
  circleColor: "#00ff00",
  thickness: 2,
  drawCenters: true,
  centerColor: "#ff0000",
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

describe("filtering_houghcircles block", () => {
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
      block.setFieldValue(0, "dp");
      block.setFieldValue(50, "dp");
      expect(block.getFieldValue("dp")).toBe(10);

      block.setFieldValue(0.1, "dp");
      expect(block.getFieldValue("dp")).toBe(0.5);

      block.setFieldValue(0, "minDist");
      expect(block.getFieldValue("minDist")).toBe(1);

      block.setFieldValue(0, "param1");
      expect(block.getFieldValue("param1")).toBe(1);

      block.setFieldValue(0, "param2");
      expect(block.getFieldValue("param2")).toBe(1);

      block.setFieldValue(-5, "minRadius");
      expect(block.getFieldValue("minRadius")).toBe(0);

      block.setFieldValue(-5, "maxRadius");
      expect(block.getFieldValue("maxRadius")).toBe(0);

      block.setFieldValue(0, "thickness");
      expect(block.getFieldValue("thickness")).toBe(1);

      block.setFieldValue(100, "thickness");
      expect(block.getFieldValue("thickness")).toBe(50);
    });
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);
      block.setFieldValue(1.5, "dp");
      block.setFieldValue(45, "minDist");
      block.setFieldValue(120, "param1");
      block.setFieldValue(35, "param2");
      block.setFieldValue(10, "minRadius");
      block.setFieldValue(80, "maxRadius");
      block.setFieldValue("#123456", "circleColor");
      block.setFieldValue(3, "thickness");
      block.setFieldValue("FALSE", "drawCenters");
      block.setFieldValue("#654321", "centerColor");
      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        dp: 1.5,
        minDist: 45,
        param1: 120,
        param2: 35,
        minRadius: 10,
        maxRadius: 80,
        circleColor: "#123456",
        thickness: 3,
        drawCenters: "FALSE",
        centerColor: "#654321",
      });
    });
  });

  it("is registered under the Filtering category in the sidebar", () => {
    const filtering = categories.find((c) => c.name === "Filtering");
    expect(filtering).toBeDefined();
    const entry = filtering?.blocks.find((b) => b.type === BLOCK_TYPE);
    expect(entry).toEqual({
      type: BLOCK_TYPE,
      label: "Hough Circle Detection",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Hough Circle Detection");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(8);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
  });
});
