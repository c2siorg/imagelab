/**
 * @vitest-environment jsdom
 */
import * as Blockly from "blockly";
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { registerAllBlocks } from "../definitions";

describe("Median Blur kernel size field", () => {
  let workspace: Blockly.Workspace;

  beforeAll(() => {
    registerAllBlocks();
  });

  afterEach(() => {
    workspace?.dispose();
  });

  function setKernelSize(value: number): number {
    workspace = new Blockly.Workspace();
    const block = workspace.newBlock("blurring_applymedianblur");
    block.setFieldValue(value, "kernelSize");
    return block.getFieldValue("kernelSize") as number;
  }

  it.each([
    [1, 3],
    [2, 3],
    [3, 3],
    [4, 5],
    [7, 7],
  ])("normalizes %d to %d", (input, expected) => {
    expect(setKernelSize(input)).toBe(expected);
  });
});
