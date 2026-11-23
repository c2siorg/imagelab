// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "filtering_stylization";

const EXPECTED_DEFAULTS: Record<string, string | number | boolean> = {
  mode: "WATERCOLOR",
  sigma_s: 60,
  sigma_r: 0.45,
  shade_factor: 0.05,
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

describe("filtering_stylization block", () => {
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

      block.setFieldValue(-10, "sigma_s");
      expect(block.getFieldValue("sigma_s")).toBe(1);

      block.setFieldValue(500, "sigma_s");
      expect(block.getFieldValue("sigma_s")).toBe(200);

      block.setFieldValue(0.001, "sigma_r");
      expect(block.getFieldValue("sigma_r")).toBe(0.01);

      block.setFieldValue(5.0, "sigma_r");
      expect(block.getFieldValue("sigma_r")).toBe(1.0);

      block.setFieldValue(0.001, "shade_factor");
      expect(block.getFieldValue("shade_factor")).toBe(0.01);

      block.setFieldValue(0.5, "shade_factor");
      expect(block.getFieldValue("shade_factor")).toBe(0.1);
    });
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);

      block.setFieldValue("PENCIL_COLOR", "mode");
      block.setFieldValue(80, "sigma_s");
      block.setFieldValue(0.08, "sigma_r");
      block.setFieldValue(0.04, "shade_factor");

      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        mode: "PENCIL_COLOR",
        sigma_s: 80,
        sigma_r: 0.08,
        shade_factor: 0.04,
      });
    });
  });

  it("is registered under the Filtering category in the sidebar", () => {
    const filtering = categories.find((c) => c.name === "Filtering");
    expect(filtering).toBeDefined();
    const entry = filtering?.blocks.find((b) => b.type === BLOCK_TYPE);
    expect(entry).toEqual({
      type: BLOCK_TYPE,
      label: "Stylization",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Non-Photorealistic Stylization");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(4);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
    expect(doc.formula).toBeDefined();
  });
});
