import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  WORKSPACE_STORAGE_KEY,
  clearPersistedWorkspace,
  loadPersistedWorkspaceState,
  saveWorkspaceState,
} from "../../src/hooks/workspacePersistence";

class LocalStorageMock implements Storage {
  public readonly store = new Map<string, string>();
  public throwOnSet = false;

  get length(): number {
    return this.store.size;
  }

  clear(): void {
    this.store.clear();
  }

  getItem(key: string): string | null {
    return this.store.has(key) ? this.store.get(key)! : null;
  }

  key(index: number): string | null {
    return Array.from(this.store.keys())[index] ?? null;
  }

  removeItem(key: string): void {
    this.store.delete(key);
  }

  setItem(key: string, value: string): void {
    if (this.throwOnSet) {
      const err = new Error("Quota exceeded");
      err.name = "QuotaExceededError";
      throw err;
    }
    this.store.set(key, value);
  }
}

describe("loadPersistedWorkspaceState", () => {
  let storage: LocalStorageMock;

  beforeEach(() => {
    storage = new LocalStorageMock();
  });

  it("returns null for expired entries and removes the key", () => {
    storage.setItem(
      WORKSPACE_STORAGE_KEY,
      JSON.stringify({
        expiresAt: Date.now() - 1000,
        data: { blocks: [] },
      }),
    );

    const result = loadPersistedWorkspaceState(storage);

    expect(result).toBeNull();
    expect(storage.getItem(WORKSPACE_STORAGE_KEY)).toBeNull();
  });

  it("returns null and removes the key for malformed JSON", () => {
    storage.setItem(WORKSPACE_STORAGE_KEY, "{not-json");

    const result = loadPersistedWorkspaceState(storage);

    expect(result).toBeNull();
    expect(storage.getItem(WORKSPACE_STORAGE_KEY)).toBeNull();
  });

  it("returns null and removes the key for missing expiresAt", () => {
    storage.setItem(
      WORKSPACE_STORAGE_KEY,
      JSON.stringify({
        data: { blocks: [] },
      }),
    );

    const result = loadPersistedWorkspaceState(storage);

    expect(result).toBeNull();
    expect(storage.getItem(WORKSPACE_STORAGE_KEY)).toBeNull();
  });

  it("returns null and removes the key for missing data", () => {
    storage.setItem(
      WORKSPACE_STORAGE_KEY,
      JSON.stringify({
        expiresAt: Date.now() + 60_000,
      }),
    );

    const result = loadPersistedWorkspaceState(storage);

    expect(result).toBeNull();
    expect(storage.getItem(WORKSPACE_STORAGE_KEY)).toBeNull();
  });

  it("returns state when payload is valid and unexpired", () => {
    const state = { blocks: [{ id: "a" }] };
    storage.setItem(
      WORKSPACE_STORAGE_KEY,
      JSON.stringify({
        expiresAt: Date.now() + 60_000,
        data: state,
      }),
    );

    const result = loadPersistedWorkspaceState<typeof state>(storage);

    expect(result).toEqual(state);
  });
});

describe("saveWorkspaceState", () => {
  let storage: LocalStorageMock;

  beforeEach(() => {
    storage = new LocalStorageMock();
  });

  it("writes payload with expiresAt in the future", () => {
    const state = { blocks: [{ id: "node-1" }] };
    const now = Date.now();
    const ok = saveWorkspaceState(state, storage, WORKSPACE_STORAGE_KEY, 10_000);

    expect(ok).toBe(true);
    const raw = storage.getItem(WORKSPACE_STORAGE_KEY);
    expect(raw).not.toBeNull();

    const payload = JSON.parse(raw!) as { expiresAt: number; data: typeof state };
    expect(payload.data).toEqual(state);
    expect(payload.expiresAt).toBeGreaterThanOrEqual(now + 10_000);
  });

  it("does not throw when localStorage throws QuotaExceededError", () => {
    storage.throwOnSet = true;
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    expect(() => saveWorkspaceState({ blocks: [] }, storage)).not.toThrow();
    expect(saveWorkspaceState({ blocks: [] }, storage)).toBe(false);

    warnSpy.mockRestore();
  });

  it("round-trips saved payload through load", () => {
    const state = { blocks: [{ id: "x" }, { id: "y" }] };
    saveWorkspaceState(state, storage, WORKSPACE_STORAGE_KEY, 60_000);

    const loaded = loadPersistedWorkspaceState<typeof state>(storage);

    expect(loaded).toEqual(state);
  });
});

describe("clearPersistedWorkspace", () => {
  it("removes the persisted key", () => {
    const storage = new LocalStorageMock();
    storage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify({ expiresAt: Date.now() + 1, data: {} }));

    clearPersistedWorkspace(storage);

    expect(storage.getItem(WORKSPACE_STORAGE_KEY)).toBeNull();
  });
});
