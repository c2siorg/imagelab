// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "transformation_convexhull";

const EXPECTED_DEFAULTS: Record<string, string | number | boolean> = {
  mode: "HULL_AND_DEFECTS",
  min_area: 50,
  min_defect_depth: 5,
  hull_color: "#00ffff",
  defect_color: "#ff0000",
  thickness: 2,
  show_contours: false,
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

describe("transformation_convexhull block", () => {
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

      block.setFieldValue(-10, "min_area");
      expect(block.getFieldValue("min_area")).toBe(0);

      block.setFieldValue(200000, "min_area");
      expect(block.getFieldValue("min_area")).toBe(100000);

      block.setFieldValue(-5, "min_defect_depth");
      expect(block.getFieldValue("min_defect_depth")).toBe(0);

      block.setFieldValue(1000, "min_defect_depth");
      expect(block.getFieldValue("min_defect_depth")).toBe(500);

      block.setFieldValue(0, "thickness");
      expect(block.getFieldValue("thickness")).toBe(1);

      block.setFieldValue(100, "thickness");
      expect(block.getFieldValue("thickness")).toBe(20);
    });
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);

      block.setFieldValue("HULL_ONLY", "mode");
      block.setFieldValue(150, "min_area");
      block.setFieldValue(12.5, "min_defect_depth");
      block.setFieldValue("#123456", "hull_color");
      block.setFieldValue("#654321", "defect_color");
      block.setFieldValue(4, "thickness");
      block.setFieldValue("TRUE", "show_contours");

      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        mode: "HULL_ONLY",
        min_area: 150,
        min_defect_depth: 12.5,
        hull_color: "#123456",
        defect_color: "#654321",
        thickness: 4,
        show_contours: "TRUE",
      });
    });
  });

  it("is registered under the Transformation category in the sidebar", () => {
    const transformation = categories.find((c) => c.name === "Transformation");
    expect(transformation).toBeDefined();
    const entry = transformation?.blocks.find((b) => b.type === BLOCK_TYPE);
    expect(entry).toEqual({
      type: BLOCK_TYPE,
      label: "Convex Hull",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Convex Hull & Defect Analysis");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(7);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
  });
});
