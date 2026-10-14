/**
 * @vitest-environment jsdom
 */
import { describe, expect, it } from "vitest";
import type * as Blockly from "blockly";
import { usePipelineStore } from "../pipelineStore";

describe("pipelineStepCount", () => {
  it("is cleared when workspace block stats are refreshed", () => {
    usePipelineStore.getState().setPipelineStepCount(3);

    usePipelineStore.getState().updateBlockStats({
      getAllBlocks: () => [],
    } as unknown as Blockly.WorkspaceSvg);

    expect(usePipelineStore.getState().pipelineStepCount).toBeNull();
  });

  it("is cleared when the store is reset", () => {
    usePipelineStore.getState().setPipelineStepCount(3);

    usePipelineStore.getState().reset();

    expect(usePipelineStore.getState().pipelineStepCount).toBeNull();
  });
});
