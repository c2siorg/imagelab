/**
 * @vitest-environment jsdom
 */
import * as Blockly from "blockly";
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { categories } from "../categories";
import { operatorDocs } from "../../data/operatorDocs";
import { registerAllBlocks } from "../definitions";

describe("HSV In-Range block", () => {
  let workspace: Blockly.Workspace;

  beforeAll(() => {
    registerAllBlocks();
  });

  afterEach(() => {
    workspace?.dispose();
  });

  it("is defined, registered, and documented", () => {
    workspace = new Blockly.Workspace();
    const block = workspace.newBlock("thresholding_inrange");
    const thresholdingCategory = categories.find(({ name }) => name === "Thresholding");

    expect(block.type).toBe("thresholding_inrange");
    expect(thresholdingCategory?.blocks).toContainEqual({
      type: "thresholding_inrange",
      label: "HSV In-Range Mask",
    });
    expect(operatorDocs.thresholding_inrange).toMatchObject({
      name: "HSV In-Range Color Masking",
      formula: expect.any(String),
      useCases: expect.arrayContaining([expect.any(String)]),
    });
  });

  it("uses the documented defaults", () => {
    workspace = new Blockly.Workspace();
    const block = workspace.newBlock("thresholding_inrange");

    expect(block.getFieldValue("h_min")).toBe(0);
    expect(block.getFieldValue("h_max")).toBe(179);
    expect(block.getFieldValue("s_min")).toBe(50);
    expect(block.getFieldValue("s_max")).toBe(255);
    expect(block.getFieldValue("v_min")).toBe(50);
    expect(block.getFieldValue("v_max")).toBe(255);
    expect(block.getFieldValue("output_mask_only")).toBe("FALSE");
  });

  it.each([
    ["h_min", -10, 0],
    ["h_max", 200, 179],
    ["s_min", -10, 0],
    ["s_max", 300, 255],
    ["v_min", -10, 0],
    ["v_max", 300, 255],
  ])("clamps %s from %d to %d", (fieldName, input, expected) => {
    workspace = new Blockly.Workspace();
    const block = workspace.newBlock("thresholding_inrange");
    block.setFieldValue(input, fieldName);

    expect(block.getFieldValue(fieldName)).toBe(expected);
  });
});
