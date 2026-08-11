import { create } from "zustand";
import * as macroApi from "../api/macros";
import * as Blockly from "blockly";
import type {
  MacroDefinition,
  MacroCreatePayload,
  MacroUpdatePayload,
  MacroVersion,
} from "../types/macro";
import { registerMacroBlock, refreshMacroBlockInstances } from "../blocks/macroBlock";

function definitionFromVersion(macro: MacroVersion): MacroDefinition {
  return {
    id: macro.macro_id,
    name: macro.name,
    owner_id: macro.owner_id,
    graph: {
      nodes: macro.pipeline_json.nodes ?? [],
      edges: macro.pipeline_json.edges ?? [],
      exposed_params: macro.pipeline_json.exposed_params,
    },
    exposedParams: macro.pipeline_json.exposed_params ?? [],
    pipeline_json: macro.pipeline_json,
    created_at: macro.created_at,
    updated_at: macro.updated_at,
  };
}

export interface MacroState {
  macros: MacroDefinition[];
  selectedMacro: MacroVersion | null;
  isLoading: boolean;
  error: string | null;
  workspace: Blockly.WorkspaceSvg | null;
  setWorkspace: (workspace: Blockly.WorkspaceSvg | null) => void;

  loadMacros: () => Promise<void>;
  loadMacroDetails: (id: string) => Promise<MacroVersion>;
  addMacro: (payload: MacroCreatePayload) => Promise<MacroVersion>;
  updateMacro: (macroId: string, updates: Partial<MacroDefinition>) => Promise<void>;
  editMacro: (id: string, payload: MacroUpdatePayload) => Promise<MacroVersion>;
  removeMacro: (id: string) => Promise<void>;
  setSelectedMacro: (macro: MacroVersion | null) => void;
  clearError: () => void;
}

export const useMacroStore = create<MacroState>((set, get) => ({
  macros: [],
  selectedMacro: null,
  isLoading: false,
  error: null,
  workspace: null,

  loadMacros: async () => {
    set({ isLoading: true, error: null });
    try {
      const macroVersions = await macroApi.fetchMacros();
      set({ macros: macroVersions.map(definitionFromVersion), isLoading: false });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load macros";
      set({ error: message, isLoading: false });
    }
  },

  loadMacroDetails: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const macroVersion = await macroApi.getMacro(id);
      const definition = definitionFromVersion(macroVersion);
      set((state) => ({
        macros: state.macros.map((macro) => (macro.id === definition.id ? definition : macro)),
        selectedMacro: macroVersion,
        isLoading: false,
      }));
      return macroVersion;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : `Failed to load macro ${id}`;
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  addMacro: async (payload: MacroCreatePayload) => {
    set({ isLoading: true, error: null });
    try {
      const created = await macroApi.createMacro(payload);
      await get().loadMacros();
      set({ selectedMacro: created, isLoading: false });
      return created;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to create macro";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  editMacro: async (id: string, payload: MacroUpdatePayload) => {
    set({ isLoading: true, error: null });
    try {
      const updated = await macroApi.updateMacro(id, payload);
      await get().loadMacros();
      set({ selectedMacro: updated, isLoading: false });
      return updated;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : `Failed to update macro ${id}`;
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  updateMacro: async (macroId, updates) => {
    const existing = get().macros.find((macro) => macro.id === macroId);
    if (!existing) {
      throw new Error(`Macro ${macroId} was not found`);
    }

    const graph = updates.graph ?? existing.graph;
    const pipelineJson = updates.pipeline_json ?? {
      nodes: graph.nodes,
      edges: graph.edges,
      exposed_params: updates.exposedParams ?? graph.exposed_params ?? existing.exposedParams ?? [],
    };

    set({ isLoading: true, error: null });
    try {
      const updated = await macroApi.updateMacro(macroId, {
        name: updates.name,
        owner_id: updates.owner_id,
        description: updates.description ?? undefined,
        pipeline_json: pipelineJson,
      });
      const definition = definitionFromVersion(updated);
      registerMacroBlock(definition);
      refreshMacroBlockInstances(get().workspace, definition);
      set((state) => ({
        macros: state.macros.map((macro) => (macro.id === macroId ? definition : macro)),
        selectedMacro: updated,
        isLoading: false,
      }));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : `Failed to update macro ${macroId}`;
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  removeMacro: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await macroApi.deleteMacro(id);
      const currentSelected = get().selectedMacro;
      if (currentSelected && currentSelected.macro_id === id) {
        set({ selectedMacro: null });
      }
      await get().loadMacros();
      set({ isLoading: false });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : `Failed to delete macro ${id}`;
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  setSelectedMacro: (macro) => set({ selectedMacro: macro }),

  setWorkspace: (workspace) => set({ workspace }),

  clearError: () => set({ error: null }),
}));
