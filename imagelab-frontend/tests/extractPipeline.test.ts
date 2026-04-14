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

// Narrow cast helper — asserts MockWorkspace satisfies the minimal interface
// that extractPipeline actually uses, without bypassing structural checking.
const ws = (w: ExtractPipelineWorkspace) => w as unknown as Parameters<typeof extractPipeline>[0];

describe("extractPipeline", () => {
  it("returns [] when there are no blocks at all", () => {
    expect(extractPipeline(ws(workspace([])))).toEqual([]);
  });

  it("returns [] if basic_readimage is not in the workspace", () => {
    // pipeline can only start from a reader block
    expect(extractPipeline(ws(workspace([block("filtering_bilateral")])))).toEqual([]);
  });

  it("handles a standalone reader block with a filename param", () => {
    const read = block("basic_readimage", [input([field("filename_label", "cat.png")])]);
    const pipeline = extractPipeline(ws(workspace([read])));
    expect(pipeline).toHaveLength(1);
    expect(pipeline[0].type).toBe("basic_readimage");
    expect(pipeline[0].params).toMatchObject({ filename_label: "cat.png" });
  });

  it("walks the chain in order: first block should come first", () => {
    const sharpen = block("filtering_sharpen", [input([field("strength", 1.2)])]);
    const morph = block("filtering_morphological", [input([field("type", "TOPHAT")])], sharpen);
    const reader = block("basic_readimage", [input([field("filename_label", "x.png")])], morph);
    const pipeline = extractPipeline(ws(workspace([reader])));
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
    const pipeline = extractPipeline(ws(workspace([reader])));
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
    const pipeline = extractPipeline(ws(workspace([read])));
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
    const pipeline = extractPipeline(ws(workspace([read])));
    expect(pipeline[1].params).toEqual({});
  });

  it("calls getTopBlocks with ordered=true — ensures pipeline order is deterministic", () => {
    // getTopBlocks(true) returns top-to-bottom order; false/undefined = insertion order
    const onGetTopBlocks = vi.fn();
    const read = block("basic_readimage", [input([field("filename_label", "x.png")])]);

    extractPipeline(ws(workspace([read], { onGetTopBlocks })));

    expect(onGetTopBlocks).toHaveBeenCalledWith(true);
  });

  it("ignores unnamed fields when extracting params", () => {
    const drawLine = block("drawingoperations_drawline", [
      input([field(undefined, "decorative label"), field("thickness", 2)]),
    ]);
    const reader = block("basic_readimage", [input([field("filename_label", "x.png")])], drawLine);

    const pipeline = extractPipeline(ws(workspace([reader])));

    expect(pipeline[1].params).toEqual({ thickness: 2 });
  });

  it("uses only the first basic_readimage chain when multiple reader blocks exist", () => {
    const r1 = block("basic_readimage", [input([field("filename_label", "a.png")])]);
    const r2 = block("basic_readimage", [input([field("filename_label", "b.png")])]);
    // extractPipeline uses find() — picks the first match; r2's chain is ignored
    const pipeline = extractPipeline(ws(workspace([r1, r2])));
    expect(pipeline).toHaveLength(1);
    expect(pipeline[0].params).toMatchObject({ filename_label: "a.png" });
  });

  it("merges only one level of VALUE-connected block params (current behaviour)", () => {
    // Documents that deep nesting (VALUE child of a VALUE child) is NOT traversed
    const innerChild = block("inner_child", [input([field("x", 10)])]);
    const outerChild = block("outer_child", [
      input([], { type: INPUT_TYPE_VALUE, connected: innerChild }),
    ]);
    const parent = block("parent_block", [
      input([], { type: INPUT_TYPE_VALUE, connected: outerChild }),
    ]);
    const read = block("basic_readimage", [input([field("filename_label", "x.png")])], parent);
    const pipeline = extractPipeline(ws(workspace([read])));
    // outerChild has no direct fieldRow, and innerChild (nested) is not traversed
    expect(pipeline[1].params).toEqual({});
  });

  it("finds basic_readimage even when it is not at index 0 of getTopBlocks", () => {
    const unrelated = block("filtering_bilateral", []);
    const reader = block("basic_readimage", [input([field("filename_label", "z.png")])]);
    // reader is at index 1 — find() still locates it regardless of position
    const pipeline = extractPipeline(ws(workspace([unrelated, reader])));
    expect(pipeline).toHaveLength(1);
    expect(pipeline[0].type).toBe("basic_readimage");
  });

  it("handles a block with an empty inputList without crashing", () => {
    // block() defaults inputList to [] — produces no params but must not throw
    const emptyBlock = block("filtering_sharpen");
    const read = block("basic_readimage", [input([field("filename_label", "x.png")])], emptyBlock);
    const pipeline = extractPipeline(ws(workspace([read])));
    expect(pipeline).toHaveLength(2);
    expect(pipeline[1].params).toEqual({});
  });
});
