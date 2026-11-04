// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "geometric_perspectivetransform";

const EXPECTED_DEFAULTS: Record<string, number> = {
  src_x1: 0,
  src_y1: 0,
  src_x2: 200,
  src_y2: 0,
  src_x3: 200,
  src_y3: 200,
  src_x4: 0,
  src_y4: 200,
  dst_x1: 0,
  dst_y1: 0,
  dst_x2: 200,
  dst_y2: 0,
  dst_x3: 200,
  dst_y3: 200,
  dst_x4: 0,
  dst_y4: 200,
  output_width: 0,
  output_height: 0,
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

describe("geometric_perspectivetransform block", () => {
  it("is defined with the backend params and their defaults", () => {
    withWorkspace((ws) => {
      const block = ws.newBlock(BLOCK_TYPE);
      for (const [name, value] of Object.entries(EXPECTED_DEFAULTS)) {
        expect(block.getFieldValue(name), name).toBe(value);
      }
    });
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);
      block.setFieldValue(10, "src_x1");
      block.setFieldValue(15, "src_y1");
      block.setFieldValue(190, "src_x2");
      block.setFieldValue(20, "src_y2");
      block.setFieldValue(185, "src_x3");
      block.setFieldValue(195, "src_y3");
      block.setFieldValue(15, "src_x4");
      block.setFieldValue(190, "src_y4");
      block.setFieldValue(0, "dst_x1");
      block.setFieldValue(0, "dst_y1");
      block.setFieldValue(300, "dst_x2");
      block.setFieldValue(0, "dst_y2");
      block.setFieldValue(300, "dst_x3");
      block.setFieldValue(400, "dst_y3");
      block.setFieldValue(0, "dst_x4");
      block.setFieldValue(400, "dst_y4");
      block.setFieldValue(300, "output_width");
      block.setFieldValue(400, "output_height");
      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        src_x1: 10,
        src_y1: 15,
        src_x2: 190,
        src_y2: 20,
        src_x3: 185,
        src_y3: 195,
        src_x4: 15,
        src_y4: 190,
        dst_x1: 0,
        dst_y1: 0,
        dst_x2: 300,
        dst_y2: 0,
        dst_x3: 300,
        dst_y3: 400,
        dst_x4: 0,
        dst_y4: 400,
        output_width: 300,
        output_height: 400,
      });
    });
  });

  it("is registered under the Geometric category in the sidebar", () => {
    const geometric = categories.find((c) => c.name === "Geometric");
    expect(geometric).toBeDefined();
    const entry = geometric?.blocks.find((b) => b.type === BLOCK_TYPE);
    expect(entry).toEqual({
      type: BLOCK_TYPE,
      label: "Perspective Transform",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Perspective Transformation");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(4);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
  });
});
