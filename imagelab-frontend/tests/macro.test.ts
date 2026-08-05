/**
 * @vitest-environment jsdom
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMacro, deleteMacro, fetchMacros, getMacro, updateMacro } from "../src/api/macros";
import { useMacroStore } from "../src/store/macroStore";
import { usePipelineStore } from "../src/store/pipelineStore";
import type { MacroItem, MacroVersion } from "../src/types/macro";

describe("Frontend Macro API Client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches macro list successfully", async () => {
    const mockMacros: MacroItem[] = [
      {
        id: "macro-123",
        name: "Test Blur Macro",
        is_macro: true,
        created_at: "2026-07-28T00:00:00Z",
        updated_at: "2026-07-28T00:00:00Z",
      },
    ];

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockMacros,
    } as Response);

    const result = await fetchMacros();
    expect(result).toEqual(mockMacros);
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/v1/macros"), expect.objectContaining({ method: "GET" }));
  });

  it("creates a macro", async () => {
    const mockVersion: MacroVersion = {
      id: "ver-1",
      macro_id: "macro-123",
      version_number: 1,
      name: "New Macro",
      workspace_json: {},
      pipeline_json: { nodes: [] },
      created_at: "2026-07-28T00:00:00Z",
      updated_at: "2026-07-28T00:00:00Z",
    };

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockVersion,
    } as Response);

    const result = await createMacro({ name: "New Macro", pipeline_json: { nodes: [] } });
    expect(result).toEqual(mockVersion);
  });

  it("retrieves a macro by ID", async () => {
    const mockVersion: MacroVersion = {
      id: "ver-1",
      macro_id: "macro-123",
      version_number: 1,
      name: "Retrieved Macro",
      workspace_json: {},
      pipeline_json: { nodes: [] },
      created_at: "2026-07-28T00:00:00Z",
      updated_at: "2026-07-28T00:00:00Z",
    };

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockVersion,
    } as Response);

    const result = await getMacro("macro-123");
    expect(result).toEqual(mockVersion);
  });

  it("updates a macro", async () => {
    const mockVersion: MacroVersion = {
      id: "ver-2",
      macro_id: "macro-123",
      version_number: 2,
      name: "Updated Macro",
      workspace_json: {},
      pipeline_json: { nodes: [] },
      created_at: "2026-07-28T00:00:00Z",
      updated_at: "2026-07-28T00:00:00Z",
    };

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockVersion,
    } as Response);

    const result = await updateMacro("macro-123", { name: "Updated Macro" });
    expect(result).toEqual(mockVersion);
  });

  it("deletes a macro", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
    } as Response);

    await expect(deleteMacro("macro-123")).resolves.not.toThrow();
  });

  it("handles macro deletion error when macro is referenced", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: false,
      status: 409,
      json: async () => ({ detail: "Cannot delete macro: referenced by active pipelines/macros" }),
    } as Response);

    await expect(deleteMacro("macro-123")).rejects.toThrow("Cannot delete macro: referenced by active pipelines/macros");
  });
});

describe("MacroStore Zustand", () => {
  beforeEach(() => {
    useMacroStore.setState({
      macros: [],
      selectedMacro: null,
      isLoading: false,
      error: null,
    });
    vi.restoreAllMocks();
  });

  it("loads macros into store", async () => {
    const mockMacros: MacroItem[] = [
      {
        id: "m-1",
        name: "Macro One",
        is_macro: true,
        created_at: "2026-07-28T00:00:00Z",
        updated_at: "2026-07-28T00:00:00Z",
      },
    ];

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockMacros,
    } as Response);

    await useMacroStore.getState().loadMacros();

    const state = useMacroStore.getState();
    expect(state.macros).toHaveLength(1);
    expect(state.macros[0].name).toBe("Macro One");
    expect(state.isLoading).toBe(false);
  });

  it("adds a new macro and reloads list", async () => {
    const mockVersion: MacroVersion = {
      id: "v-1",
      macro_id: "m-2",
      version_number: 1,
      name: "Macro Two",
      workspace_json: {},
      pipeline_json: {},
      created_at: "2026-07-28T00:00:00Z",
      updated_at: "2026-07-28T00:00:00Z",
    };

    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockVersion,
      } as Response) // create call
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [
          { id: "m-2", name: "Macro Two", is_macro: true, created_at: "", updated_at: "" },
        ],
      } as Response); // reload list call

    const res = await useMacroStore.getState().addMacro({ name: "Macro Two", pipeline_json: {} });
    expect(res).toEqual(mockVersion);
    expect(useMacroStore.getState().selectedMacro).toEqual(mockVersion);
  });
});

describe("PipelineStore Macro Step Result Lookup", () => {
  beforeEach(() => {
    usePipelineStore.getState().reset();
  });

  it("looks up step result by exact block ID or parent macro prefix", () => {
    const results = [
      { index: 1, block_id: "step_1", type: "basic_readimage", success: true },
      { index: 2, block_id: "m1_node:blur_1", type: "blurring_applyblur", success: true },
      { index: 3, block_id: "m1_node:canny_1", type: "filtering_cannyedge", success: true },
    ];

    usePipelineStore.getState().setStepResults(results);

    // Exact match
    const exact = usePipelineStore.getState().getStepResultByBlockId("step_1");
    expect(exact?.type).toBe("basic_readimage");

    // Parent block ID match for macro block "m1_node" (returns last executed internal step)
    const macroResult = usePipelineStore.getState().getStepResultByBlockId("m1_node");
    expect(macroResult).toBeDefined();
    expect(macroResult?.block_id).toBe("m1_node:canny_1");
    expect(macroResult?.type).toBe("filtering_cannyedge");
  });
});
