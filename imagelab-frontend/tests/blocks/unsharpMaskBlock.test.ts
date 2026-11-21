// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, describe, expect, it } from "vitest";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { categories } from "../../src/blocks/categories";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { operatorDocs } from "../../src/data/operatorDocs";
import { extractPipeline } from "../../src/hooks/usePipeline";

const BLOCK_TYPE = "filtering_unsharpmask";

const EXPECTED_DEFAULTS: Record<string, number> = {
  kernel_size: 5,
  sigma: 1.0,
  amount: 1.5,
  threshold: 0,
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

describe("filtering_unsharpmask block", () => {
  it("is defined with the backend params and their defaults", () => {
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

      block.setFieldValue(1, "kernel_size");
      expect(block.getFieldValue("kernel_size")).toBe(3);

      block.setFieldValue(100, "kernel_size");
      expect(block.getFieldValue("kernel_size")).toBe(31);

      block.setFieldValue(0.01, "sigma");
      expect(block.getFieldValue("sigma")).toBe(0.1);

      block.setFieldValue(50, "sigma");
      expect(block.getFieldValue("sigma")).toBe(10.0);

      block.setFieldValue(0.01, "amount");
      expect(block.getFieldValue("amount")).toBe(0.1);

      block.setFieldValue(20, "amount");
      expect(block.getFieldValue("amount")).toBe(5.0);

      block.setFieldValue(-5, "threshold");
      expect(block.getFieldValue("threshold")).toBe(0);

      block.setFieldValue(200, "threshold");
      expect(block.getFieldValue("threshold")).toBe(50);
    });
  });

  it("extracts its params into a pipeline step after a read image block", () => {
    withWorkspace((ws) => {
      const reader = ws.newBlock("basic_readimage");
      const block = ws.newBlock(BLOCK_TYPE);

      block.setFieldValue(7, "kernel_size");
      block.setFieldValue(1.5, "sigma");
      block.setFieldValue(2.0, "amount");
      block.setFieldValue(5, "threshold");

      reader.nextConnection?.connect(block.previousConnection!);

      const pipeline = extractPipeline(ws as unknown as Blockly.WorkspaceSvg);
      const step = pipeline.find((s) => s.type === BLOCK_TYPE);
      expect(step).toBeDefined();
      expect(step?.params).toEqual({
        kernel_size: 7,
        sigma: 1.5,
        amount: 2.0,
        threshold: 5,
      });
    });
  });

  it("is registered under the Filtering category in the sidebar", () => {
    const filtering = categories.find((c) => c.name === "Filtering");
    expect(filtering).toBeDefined();
    const entry = filtering?.blocks.find((b) => b.type === BLOCK_TYPE);
    expect(entry).toEqual({
      type: BLOCK_TYPE,
      label: "Unsharp Masking",
    });
  });

  it("has documentation in operatorDocs", () => {
    const doc = operatorDocs[BLOCK_TYPE];
    expect(doc).toBeDefined();
    expect(doc.name).toBe("Unsharp Masking");
    expect(doc.parameters.length).toBeGreaterThanOrEqual(4);
    expect(doc.useCases.length).toBeGreaterThanOrEqual(1);
  });
});
