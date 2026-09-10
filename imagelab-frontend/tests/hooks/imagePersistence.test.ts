import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  clearPersistedImage,
  IMAGE_STORAGE_KEY,
  loadPersistedImageState,
  saveImageState,
} from "../../src/hooks/imagePersistence";

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

describe("loadPersistedImageState", () => {
  let storage: LocalStorageMock;

  beforeEach(() => {
    storage = new LocalStorageMock();
  });

  it("returns null for expired entries and removes the key", () => {
    storage.setItem(
      IMAGE_STORAGE_KEY,
      JSON.stringify({
        expiresAt: Date.now() - 1000,
        data: { image: "abc", format: "png", filename: "cat.png" },
      }),
    );

    const result = loadPersistedImageState(storage);

    expect(result).toBeNull();
    expect(storage.getItem(IMAGE_STORAGE_KEY)).toBeNull();
  });

  it("returns null and removes the key for malformed JSON", () => {
    storage.setItem(IMAGE_STORAGE_KEY, "{not-json");

    const result = loadPersistedImageState(storage);

    expect(result).toBeNull();
    expect(storage.getItem(IMAGE_STORAGE_KEY)).toBeNull();
  });

  it("returns null and removes the key for invalid payloads", () => {
    storage.setItem(
      IMAGE_STORAGE_KEY,
      JSON.stringify({
        expiresAt: Date.now() + 60_000,
        data: { image: "abc", filename: "cat.png" },
      }),
    );

    const result = loadPersistedImageState(storage);

    expect(result).toBeNull();
    expect(storage.getItem(IMAGE_STORAGE_KEY)).toBeNull();
  });

  it("returns image state when payload is valid and unexpired", () => {
    const state = { image: "abc123", format: "png", filename: "cat.png" };
    storage.setItem(
      IMAGE_STORAGE_KEY,
      JSON.stringify({
        expiresAt: Date.now() + 60_000,
        data: state,
      }),
    );

    const result = loadPersistedImageState(storage);

    expect(result).toEqual(state);
  });
});

describe("saveImageState", () => {
  let storage: LocalStorageMock;

  beforeEach(() => {
    storage = new LocalStorageMock();
  });

  it("writes payload with expiresAt in the future", () => {
    const state = { image: "abc123", format: "png", filename: "cat.png" };
    const now = Date.now();
    const ok = saveImageState(state, storage, IMAGE_STORAGE_KEY, 10_000);

    expect(ok).toBe(true);
    const raw = storage.getItem(IMAGE_STORAGE_KEY);
    expect(raw).not.toBeNull();

    const payload = JSON.parse(raw!) as { expiresAt: number; data: typeof state };
    expect(payload.data).toEqual(state);
    expect(payload.expiresAt).toBeGreaterThanOrEqual(now + 10_000);
  });

  it("does not throw when localStorage throws QuotaExceededError", () => {
    storage.throwOnSet = true;
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    expect(() => saveImageState({ image: "abc", format: "png", filename: null }, storage)).not.toThrow();
    expect(saveImageState({ image: "abc", format: "png", filename: null }, storage)).toBe(false);

    warnSpy.mockRestore();
  });

  it("skips oversized images", () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    const ok = saveImageState(
      { image: "a".repeat(3_500_001), format: "png", filename: "huge.png" },
      storage,
    );

    expect(ok).toBe(false);
    expect(storage.getItem(IMAGE_STORAGE_KEY)).toBeNull();
    warnSpy.mockRestore();
  });
});

describe("clearPersistedImage", () => {
  it("removes the persisted key", () => {
    const storage = new LocalStorageMock();
    storage.setItem(
      IMAGE_STORAGE_KEY,
      JSON.stringify({
        expiresAt: Date.now() + 1,
        data: { image: "abc", format: "png", filename: "cat.png" },
      }),
    );

    clearPersistedImage(storage);

    expect(storage.getItem(IMAGE_STORAGE_KEY)).toBeNull();
  });
});
