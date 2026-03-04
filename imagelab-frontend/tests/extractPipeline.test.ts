import { describe, expect, it, vi } from "vitest";
import { extractPipeline } from "../src/hooks/usePipeline";
import {
  block,
  field,
  input,
  INPUT_TYPE_VALUE,
  workspace,
} from "./blocklyMockFactory";
import type { ExtractPipelineWorkspace } from "./blocklyMockFactory";

describe("extractPipeline", () => {
  it("returns [] when there are no blocks at all", () => {
    const ws: ExtractPipelineWorkspace = workspace([]);
    expect(extractPipeline(ws)).toEqual([]);
  });

  it("returns [] if basic_readimage is not in the workspace", () => {
    // pipeline can only start from a reader block
    const ws: ExtractPipelineWorkspace = workspace([block("filtering_bilateral")]);
    expect(extractPipeline(ws)).toEqual([]);
  });

  it("handles a standalone reader block with a filename param", () => {
    const read = block("basic_readimage", [input([field("filename_label", "cat.png")])]);
    const ws: ExtractPipelineWorkspace = workspace([read]);
    const pipeline = extractPipeline(ws);
    expect(pipeline).toHaveLength(1);
    expect(pipeline[0].type).toBe("basic_readimage");
    expect(pipeline[0].params).toMatchObject({ filename_label: "cat.png" });
  });

  it("walks the chain in order: first block should come first", () => {
    const sharpen = block("filtering_sharpen", [input([field("strength", 1.2)])]);
    const morph = block("filtering_morphological", [input([field("type", "TOPHAT")])], sharpen);
    const reader = block("basic_readimage", [input([field("filename_label", "x.png")])], morph);
    const ws: ExtractPipelineWorkspace = workspace([reader]);
    const pipeline = extractPipeline(ws);
    expect(pipeline.map((s) => s.type)).toEqual([
      "basic_readimage",
      "filtering_morphological",
      "filtering_sharpen",
    ]);
    expect(pipeline[1].params).toMatchObject({ type: "TOPHAT" }); // dropdown field check
  });

  it("picks up numeric and color field values from a drawing block", () => {
    const drawLine = block("drawingoperations_drawline", [
      input([field("thickness", 2), field("rgbcolors_input", "#ff00ff")]),
    ]);
    const reader = block("basic_readimage", [input([field("filename_label", "x.png")])], drawLine);
    const ws: ExtractPipelineWorkspace = workspace([reader]);
    const pipeline = extractPipeline(ws);
    expect(pipeline[1].params).toMatchObject({ thickness: 2, rgbcolors_input: "#ff00ff" });
  });

  it("pulls params from VALUE-connected blocks", () => {
    const borderEachSide = block("border_each_side", [
      input([
        field("borderTop", 3),
        field("borderLeft", 4),
        field("borderRight", 5),
        field("borderBottom", 6),
      ]),
    ]);
    const applyBorders = block("thresholding_applyborders", [
      input([], { type: INPUT_TYPE_VALUE, connected: borderEachSide }),
    ]);
    const read = block(
      "basic_readimage",
      [input([field("filename_label", "x.png")])],
      applyBorders,
    );
    const ws: ExtractPipelineWorkspace = workspace([read]);
    const pipeline = extractPipeline(ws);
    expect(pipeline.map((s) => s.type)).toEqual(["basic_readimage", "thresholding_applyborders"]);
    expect(pipeline[1].params).toMatchObject({
      borderTop: 3,
      borderLeft: 4,
      borderRight: 5,
      borderBottom: 6,
    });
  });

  it("ignores connected blocks when the input type is not VALUE (type 1)", () => {
    // type: 2 is a statement input, should not be followed
    const child = block("border_for_all", [input([field("border_all_sides", 9)])]);
    const parent = block("some_parent", [input([], { type: 2, connected: child })]);
    const read = block("basic_readimage", [input([field("filename_label", "x.png")])], parent);
    const ws: ExtractPipelineWorkspace = workspace([read]);
    const pipeline = extractPipeline(ws);
    expect(pipeline[1].params).toEqual({});
  });

  it("calls getTopBlocks with ordered=true", () => {
    const onGetTopBlocks = vi.fn();
    const read = block("basic_readimage", [input([field("filename_label", "x.png")])]);

    extractPipeline(workspace([read], { onGetTopBlocks }));

    expect(onGetTopBlocks).toHaveBeenCalledWith(true);
  });

  it("ignores unnamed fields when extracting params", () => {
    const drawLine = block("drawingoperations_drawline", [
      input([field(undefined, "decorative label"), field("thickness", 2)]),
    ]);
    const reader = block("basic_readimage", [input([field("filename_label", "x.png")])], drawLine);

    const ws: ExtractPipelineWorkspace = workspace([reader]);
    const pipeline = extractPipeline(ws);

    expect(pipeline[1].params).toEqual({ thickness: 2 });
  });
});
