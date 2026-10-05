// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "filtering_houghlines";

// Field names must match the keys the backend operator reads from params.
const EXPECTED_DEFAULTS: Record<string, string | number> = {
  rho: 1,
  thetaDegrees: 1,
  threshold: 50,
  minLineLength: 50,
  maxLineGap: 10,
  color: "#00ff00",
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

describe("filtering_houghlines block", () => {
  it("is defined with the seven backend params and their defaults", () => {
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
      block.setFieldValue(0, "rho");
      block.setFieldValue(500, "thetaDegrees");
      block.setFieldValue(0, "threshold");
      block.setFieldValue(-5, "minLineLength");
      block.setFieldValue(-5, "maxLineGap");
      block.setFieldValue(0, "thickness");

      expect(block.getFieldValue("rho")).toBe(0.1);
      expect(block.getFieldValue("thetaDegrees")).toBe(180);
      expect(block.getFieldValue("threshold")).toBe(1);
      expect(block.getFieldValue("minLineLength")).toBe(0);
      expect(block.getFieldValue("maxLineGap")).toBe(0);
      expect(block.getFieldValue("thickness")).toBe(1);
    });
  });

  it("is listed in the Filtering toolbox category", () => {
    const filtering = categories.find((c) => c.name === "Filtering");
    expect(filtering).toBeDefined();
    expect(filtering?.blocks).toContainEqual({
      type: BLOCK_TYPE,
      label: "Hough Line Detection",
    });
  });

  it("has operator docs covering every param", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Hough Line Detection");
    expect(doc.parameters).toHaveLength(Object.keys(EXPECTED_DEFAULTS).length);
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const hough = ws.newBlock(BLOCK_TYPE);
      hough.setFieldValue(2, "rho");
      hough.setFieldValue("#ff0000", "color");
      reader.nextConnection?.connect(hough.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toMatchObject({ ...EXPECTED_DEFAULTS, rho: 2, color: "#ff0000" });
    });
  });
});
