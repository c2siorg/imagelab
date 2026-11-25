// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "filtering_lsd";

const EXPECTED_DEFAULTS: Record<string, string | number> = {
  refine: "STD",
  scale: 0.8,
  lineColor: "#00ff00",
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

describe("filtering_lsd block", () => {
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

      block.setFieldValue(0.01, "scale");
      expect(block.getFieldValue("scale")).toBe(0.1);
      block.setFieldValue(10, "scale");
      expect(block.getFieldValue("scale")).toBe(2.0);

      block.setFieldValue(0, "thickness");
      expect(block.getFieldValue("thickness")).toBe(1);
      block.setFieldValue(50, "thickness");
      expect(block.getFieldValue("thickness")).toBe(20);
    });
  });

  it("supports refine dropdown choices", () => {
    withWorkspace((ws) => {
      const block = ws.newBlock(BLOCK_TYPE);
      block.setFieldValue("NONE", "refine");
      expect(block.getFieldValue("refine")).toBe("NONE");
      block.setFieldValue("ADV", "refine");
      expect(block.getFieldValue("refine")).toBe("ADV");
      block.setFieldValue("STD", "refine");
      expect(block.getFieldValue("refine")).toBe("STD");
    });
  });

  it("is listed in the Filtering toolbox category", () => {
    const filtering = categories.find((c) => c.name === "Filtering");
    expect(filtering).toBeDefined();
    expect(filtering?.blocks).toContainEqual({
      type: BLOCK_TYPE,
      label: "Line Segment Detector",
    });
  });

  it("has operator docs covering every param", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Line Segment Detector (LSD)");
    expect(doc.parameters).toHaveLength(Object.keys(EXPECTED_DEFAULTS).length);
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);
      block.setFieldValue("ADV", "refine");
      block.setFieldValue(1.2, "scale");
      block.setFieldValue("#ff0000", "lineColor");
      block.setFieldValue(4, "thickness");
      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        refine: "ADV",
        scale: 1.2,
        lineColor: "#ff0000",
        thickness: 4,
      });
    });
  });
});
