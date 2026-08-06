import { create } from "zustand";
import * as macroApi from "../api/macros";
import type {
  MacroDefinition,
  MacroCreatePayload,
  MacroUpdatePayload,
  MacroVersion,
} from "../types/macro";

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
    created_at: macro.created_at,
    updated_at: macro.updated_at,
  };
}

export interface MacroState {
  macros: MacroDefinition[];
  selectedMacro: MacroVersion | null;
  isLoading: boolean;
  error: string | null;

  loadMacros: () => Promise<void>;
  loadMacroDetails: (id: string) => Promise<MacroVersion>;
  addMacro: (payload: MacroCreatePayload) => Promise<MacroVersion>;
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

  loadMacros: async () => {
    set({ isLoading: true, error: null });
    try {
      const macroItems = await macroApi.fetchMacros();
      const macroVersions = await Promise.all(
        macroItems.map((macro) => macroApi.getMacro(macro.id)),
      );
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

  clearError: () => set({ error: null }),
}));
