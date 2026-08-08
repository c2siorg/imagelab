import { beforeEach, describe, expect, it } from "vitest";
import { useMacroStore } from "../../store/useMacroStore";
import { findDependentMacros } from "../macroDependencies";

describe("findDependentMacros", () => {
  beforeEach(() => {
    useMacroStore.setState({
      macros: [
        { id: "child", name: "Child", graph: { nodes: [], edges: [] } },
        {
          id: "parent",
          name: "Parent",
          graph: {
            nodes: [{ id: "use-child", type: "macro_child", params: { blur__kernel: 5 } }],
            edges: [],
          },
        },
        {
          id: "unrelated",
          name: "Unrelated",
          graph: {
            nodes: [{ id: "use-child", type: "macro_child", params: { threshold__kernel: 3 } }],
            edges: [],
          },
        },
      ],
    });
  });

  it("matches only the exact serialized exposed-field key", () => {
    expect(findDependentMacros("child", ["blur__kernel"]).map((macro) => macro.id)).toEqual([
      "parent",
    ]);
  });

  it("returns no dependents for an unrelated field", () => {
    expect(findDependentMacros("child", ["blur__sigma"])).toEqual([]);
  });
});
