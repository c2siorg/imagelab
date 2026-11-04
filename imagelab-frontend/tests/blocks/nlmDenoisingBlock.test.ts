// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "filtering_nlmdenoising";

const EXPECTED_DEFAULTS: Record<string, number> = {
  h: 10,
  hColor: 10,
  templateWindowSize: 7,
  searchWindowSize: 21,
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

describe("filtering_nlmdenoising block", () => {
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

      block.setFieldValue(0, "h");
      expect(block.getFieldValue("h")).toBe(0.5);
      block.setFieldValue(200, "h");
      expect(block.getFieldValue("h")).toBe(100);

      block.setFieldValue(0, "hColor");
      expect(block.getFieldValue("hColor")).toBe(0.5);
      block.setFieldValue(200, "hColor");
      expect(block.getFieldValue("hColor")).toBe(100);

      block.setFieldValue(1, "templateWindowSize");
      expect(block.getFieldValue("templateWindowSize")).toBe(3);
      block.setFieldValue(50, "templateWindowSize");
      expect(block.getFieldValue("templateWindowSize")).toBe(21);

      block.setFieldValue(2, "searchWindowSize");
      expect(block.getFieldValue("searchWindowSize")).toBe(5);
      block.setFieldValue(100, "searchWindowSize");
      expect(block.getFieldValue("searchWindowSize")).toBe(45);
    });
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);
      block.setFieldValue(15, "h");
      block.setFieldValue(12, "hColor");
      block.setFieldValue(9, "templateWindowSize");
      block.setFieldValue(25, "searchWindowSize");
      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        h: 15,
        hColor: 12,
        templateWindowSize: 9,
        searchWindowSize: 25,
      });
    });
  });

  it("is registered under the Filtering category in the sidebar", () => {
    const filtering = categories.find((c) => c.name === "Filtering");
    expect(filtering).toBeDefined();
    const entry = filtering?.blocks.find((b) => b.type === BLOCK_TYPE);
    expect(entry).toEqual({
      type: BLOCK_TYPE,
      label: "NLM Denoising",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Non-Local Means Denoising");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(4);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
  });
});
