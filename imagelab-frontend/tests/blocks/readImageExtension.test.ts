// @vitest-environment jsdom
import * as Blockly from "blockly";
import { beforeAll, beforeEach, describe, expect, it } from "vitest";
import {
  markWorkspaceTearingDown,
  registerReadImageExtension,
} from "../../src/blocks/extensions/readImageExtension";
import { usePipelineStore } from "../../src/store/pipelineStore";

const TEST_BLOCK = "test_read_image";

beforeAll(() => {
  registerReadImageExtension();
  Blockly.common.defineBlocksWithJsonArray([
    {
      type: TEST_BLOCK,
      message0: "Read image %1",
      args0: [{ type: "field_label_serializable", name: "filename_label", text: "No image" }],
      extensions: ["read_image_upload"],
    },
  ]);
});

describe("read image block disposal", () => {
  beforeEach(() => {
    localStorage.clear();
    usePipelineStore.getState().clearImage();
  });

  it("clears the image when the block is deleted", () => {
    const ws = new Blockly.Workspace();
    const block = ws.newBlock(TEST_BLOCK);
    usePipelineStore.getState().setOriginalImage("abc", "png", "Main.png");
    block.dispose(false);
    expect(usePipelineStore.getState().originalImage).toBeNull();
    ws.dispose();
  });

  it("keeps the image when the workspace is torn down", () => {
    const ws = new Blockly.Workspace();
    ws.newBlock(TEST_BLOCK);
    usePipelineStore.getState().setOriginalImage("abc", "png", "Main.png");
    markWorkspaceTearingDown(ws);
    ws.dispose();
    expect(usePipelineStore.getState().originalImage).toBe("abc");
  });
});
