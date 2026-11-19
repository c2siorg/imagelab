// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "transformation_minenclosing";

const EXPECTED_DEFAULTS: Record<string, string | number | boolean> = {
  geometry: "ROTATED_BOX",
  min_area: 50,
  box_color: "#00ffff",
  circle_color: "#ff00ff",
  ellipse_color: "#ffff00",
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

describe("transformation_minenclosing block", () => {
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

      block.setFieldValue("ALL_SHAPES", "geometry");
      block.setFieldValue(120, "min_area");
      block.setFieldValue("#123456", "box_color");
      block.setFieldValue("#654321", "circle_color");
      block.setFieldValue("#abcdef", "ellipse_color");
      block.setFieldValue(4, "thickness");
      block.setFieldValue("TRUE", "show_contours");

      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        geometry: "ALL_SHAPES",
        min_area: 120,
        box_color: "#123456",
        circle_color: "#654321",
        ellipse_color: "#abcdef",
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
      label: "Minimum Enclosing Geometries",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Minimum Enclosing Geometries");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(7);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
  });
});
