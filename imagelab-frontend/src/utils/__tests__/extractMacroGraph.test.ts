import { describe, expect, it } from "vitest";
import type * as Blockly from "blockly";
import {
  extractExposedParamCandidates,
  extractMacroGraph,
  getSelectedBlocks,
  hasMacroCycle,
} from "../extractMacroGraph";
import { useMacroStore } from "../../store/useMacroStore";

const INPUT_TYPE_VALUE = 1;

type MockField = {
  name?: string;
  getValue: () => unknown;
};

type MockInput = {
  name?: string;
  fieldRow: MockField[];
  type: number;
  connection: { targetBlock: () => MockBlock | null };
};

type MockBlock = {
  id: string;
  type: string;
  inputList: MockInput[];
  getNextBlock: () => MockBlock | null;
  getDescendants?: (ordered?: boolean) => MockBlock[];
};

function createMockField(name?: string, value?: unknown): MockField {
  return { name, getValue: () => value };
}

function createMockInput(
  name?: string,
  fieldRow: MockField[] = [],
  opts?: { type?: number; connected?: MockBlock | null },
): MockInput {
  return {
    name,
    fieldRow,
    type: opts?.type ?? 0,
    connection: { targetBlock: () => opts?.connected ?? null },
  };
}

function createMockBlock(
  id: string,
  type: string,
  inputList: MockInput[] = [],
  next: MockBlock | null = null,
): MockBlock {
  const block: MockBlock = {
    id,
    type,
    inputList,
    getNextBlock: () => next,
  };
  block.getDescendants = () => {
    const list: MockBlock[] = [block];
    let curr = next;
    while (curr) {
      list.push(curr);
      curr = curr.getNextBlock();
    }
    return list;
  };
  return block;
}

describe("extractMacroGraph", () => {
  it("throws an error when selecting fewer than two blocks", () => {
    const b1 = createMockBlock("b1", "filtering_blur") as unknown as Blockly.Block;
    expect(() => extractMacroGraph([])).toThrow(
      "At least two blocks must be selected to create a macro",
    );
    expect(() => extractMacroGraph([b1])).toThrow(
      "At least two blocks must be selected to create a macro",
    );
  });

  it("extracts a valid linear chain of connected blocks", () => {
    const b2 = createMockBlock("b2", "filtering_cannyedge", [
      createMockInput(undefined, [createMockField("threshold1", 100)]),
    ]);

    const b1 = createMockBlock(
      "b1",
      "filtering_gaussianblur",
      [createMockInput(undefined, [createMockField("kernel_size", 5)])],
      b2,
    ) as unknown as Blockly.Block;

    const selected = [b1, b2 as unknown as Blockly.Block];
    const graph = extractMacroGraph(selected);

    expect(graph.nodes).toHaveLength(2);
    expect(graph.nodes[0]).toEqual({
      id: "b1",
      type: "filtering_gaussianblur",
      op: "filtering_gaussianblur",
      params: { kernel_size: 5 },
    });
    expect(graph.nodes[1]).toEqual({
      id: "b2",
      type: "filtering_cannyedge",
      op: "filtering_cannyedge",
      params: { threshold1: 100 },
    });

    expect(graph.edges).toHaveLength(1);
    expect(graph.edges[0]).toEqual({
      from: "b1",
      to: "b2",
    });
  });

  it("extracts multi-input / split value connection edges", () => {
    const sourceBlock = createMockBlock("src1", "image_source", [
      createMockInput(undefined, [createMockField("src_val", "active")]),
    ]);

    const targetBlock = createMockBlock("tgt1", "blend_images", [
      createMockInput("image", [], { type: INPUT_TYPE_VALUE, connected: sourceBlock }),
      createMockInput(undefined, [createMockField("alpha", 0.5)]),
    ]);

    const selected = [
      sourceBlock as unknown as Blockly.Block,
      targetBlock as unknown as Blockly.Block,
    ];
    const graph = extractMacroGraph(selected);

    expect(graph.nodes).toHaveLength(2);
    expect(graph.edges).toHaveLength(1);
    expect(graph.edges[0]).toEqual({
      from: "src1",
      to: "tgt1",
      input_port: "image",
    });
  });

  it("throws error on disconnected / floating block selections", () => {
    const b1 = createMockBlock("b1", "filtering_gaussianblur") as unknown as Blockly.Block;
    const b2 = createMockBlock("b2", "filtering_cannyedge") as unknown as Blockly.Block;

    expect(() => extractMacroGraph([b1, b2])).toThrow(
      "Selection contains floating/unconnected blocks",
    );
  });

  it("extracts candidate exposed parameters correctly", () => {
    const b1 = createMockBlock("b1", "filtering_gaussianblur", [
      createMockInput(undefined, [createMockField("kernel_size", 5)]),
    ]) as unknown as Blockly.Block;

    const b2 = createMockBlock("b2", "filtering_cannyedge", [
      createMockInput(undefined, [createMockField("low", 10), createMockField("high", 20)]),
    ]) as unknown as Blockly.Block;

    const candidates = extractExposedParamCandidates([b1, b2]);

    expect(candidates).toHaveLength(3);
    expect(candidates[0]).toEqual({
      blockId: "b1",
      blockType: "filtering_gaussianblur",
      paramName: "kernel_size",
      label: "kernel_size (Gaussianblur)",
      defaultValue: 5,
    });
    expect(candidates[1].paramName).toBe("low");
    expect(candidates[2].paramName).toBe("high");
  });

  it("excludes Read Image blocks and static UI fields from macro data", () => {
    const b2 = createMockBlock("b2", "canny") as unknown as Blockly.Block;
    const b1 = createMockBlock(
      "b1",
      "blur",
      [
        createMockInput(undefined, [
          createMockField("kernel", 5),
          createMockField("MACRO_NAME", "Blur"),
        ]),
      ],
      b2 as unknown as MockBlock,
    ) as unknown as Blockly.Block;
    const read = createMockBlock(
      "read",
      "basic_readimage",
      [],
      b1 as unknown as MockBlock,
    ) as unknown as Blockly.Block;

    expect(extractMacroGraph([read, b1, b2]).nodes.map((node) => node.id)).toEqual(["b1", "b2"]);
    expect(extractExposedParamCandidates([read, b1, b2])).toHaveLength(1);
  });

  it("cleans nested macro parameter labels", () => {
    const nested = createMockBlock("nested", "macro-child", [
      createMockInput(undefined, [createMockField("|PB=inner__filterSize", 5)]),
    ]) as unknown as Blockly.Block;

    expect(extractExposedParamCandidates([nested])[0].label).toBe("filterSize (macro-child)");
  });

  it("detects direct and transitive saved macro cycles", () => {
    useMacroStore.setState({
      macros: [
        { id: "a", name: "A", graph: { nodes: [{ id: "b", type: "macro_b" }], edges: [] } },
        { id: "b", name: "B", graph: { nodes: [{ id: "a", type: "macro_a" }], edges: [] } },
      ],
    });
    const selected = createMockBlock("selected", "macro_a") as unknown as Blockly.Block;

    expect(hasMacroCycle("a", [selected])).toBe(true);
    expect(hasMacroCycle("missing", [selected])).toBe(true);

    useMacroStore.setState({
      macros: [
        { id: "a", name: "A", graph: { nodes: [{ id: "b", type: "macro_b" }], edges: [] } },
        { id: "b", name: "B", graph: { nodes: [], edges: [] } },
      ],
    });
    expect(hasMacroCycle("a", [selected])).toBe(false);
  });

  it("gets selected blocks and descendants from workspace", () => {
    const mockWs = {} as unknown as Blockly.WorkspaceSvg;

    expect(getSelectedBlocks(null)).toEqual([]);
    expect(getSelectedBlocks(mockWs)).toEqual([]);
  });

  it("extracts macro_blend block statement branches and parameters cleanly", () => {
    const child1 = createMockBlock("c1", "imageconvertions_grayimage");
    const child2 = createMockBlock("c2", "blurring_applyblur");

    const blendBlock = createMockBlock("blend1", "macro_blend", [
      createMockInput(undefined, [createMockField("alpha", 0.7)]),
      createMockInput("OP1", [], { type: 3, connected: child1 }),
      createMockInput("OP2", [], { type: 3, connected: child2 }),
    ]);

    const downstreamBlock = createMockBlock("down1", "filtering_cannyedge");
    (blendBlock as unknown as { getNextBlock: () => MockBlock | null }).getNextBlock = () =>
      downstreamBlock;

    const graph = extractMacroGraph([
      blendBlock as unknown as Blockly.Block,
      downstreamBlock as unknown as Blockly.Block,
    ]);

    expect(graph.nodes).toHaveLength(2);

    const blendNode = graph.nodes[0];
    expect(blendNode?.type).toBe("macro_blend");
    expect(blendNode?.params?.alpha).toBe(0.7);

    const op1Branch = (blendNode?.params?.op1_branch ?? []) as MockBlock[];
    const op2Branch = (blendNode?.params?.op2_branch ?? []) as MockBlock[];

    expect(op1Branch).toBeDefined();
    expect(op2Branch).toBeDefined();
    expect(op1Branch[0]?.type).toBe("imageconvertions_grayimage");
    expect(op2Branch[0]?.type).toBe("blurring_applyblur");
  });

  it("extracts macro_if_else block statement branches and parameters cleanly", () => {
    const ifChild = createMockBlock("ic1", "imageconvertions_grayimage");
    const elseChild = createMockBlock("ec1", "blurring_applyblur");

    const ifElseBlock = createMockBlock("ifelse1", "macro_if_else", [
      createMockInput(undefined, [
        createMockField("metric", "mean_brightness"),
        createMockField("comparator", ">"),
        createMockField("threshold", 128),
      ]),
      createMockInput("IF_BRANCH", [], { type: 3, connected: ifChild }),
      createMockInput("ELSE_BRANCH", [], { type: 3, connected: elseChild }),
    ]);

    const downstreamBlock = createMockBlock("down2", "filtering_cannyedge");
    (ifElseBlock as unknown as { getNextBlock: () => MockBlock | null }).getNextBlock = () =>
      downstreamBlock;

    const graph = extractMacroGraph([
      ifElseBlock as unknown as Blockly.Block,
      downstreamBlock as unknown as Blockly.Block,
    ]);

    expect(graph.nodes).toHaveLength(2);
    expect(graph.nodes[0]!.type).toBe("macro_if_else");
    expect(graph.nodes[0]!.params!.metric).toBe("mean_brightness");
    expect(graph.nodes[0]!.params!.comparator).toBe(">");
    expect(graph.nodes[0]!.params!.threshold).toBe(128);
    expect(graph.nodes[0]!.params!.if_branch).toBeDefined();
    expect(graph.nodes[0]!.params!.else_branch).toBeDefined();
  });
});
