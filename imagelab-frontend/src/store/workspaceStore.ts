import { create } from "zustand";

export interface SavedWorkspace {
  id: string;
  name: string;
  data: Record<string, unknown>;
  createdAt: number;
}

interface WorkspaceState {
  workspaces: SavedWorkspace[];
  loadWorkspaces: () => void;
  saveWorkspace: (name: string, data: Record<string, unknown>) => void;
  deleteWorkspace: (id: string) => void;
}

const STORAGE_KEY = "imagelab_workspaces";

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  workspaces: [],
  loadWorkspaces: () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        set({ workspaces: JSON.parse(stored) });
      }
    } catch (e) {
      console.error("Failed to load workspaces", e);
    }
  },
  saveWorkspace: (name, data) => {
    set((state) => {
      const newWorkspace: SavedWorkspace = {
        id: crypto.randomUUID(),
        name,
        data,
        createdAt: Date.now(),
      };
      const updated = [newWorkspace, ...state.workspaces];
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return { workspaces: updated };
    });
  },
  deleteWorkspace: (id) => {
    set((state) => {
      const updated = state.workspaces.filter((w) => w.id !== id);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return { workspaces: updated };
    });
  },
}));
