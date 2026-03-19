export const WORKSPACE_STORAGE_KEY = "imagelab.pipeline.workspace.v1";
export const WORKSPACE_STORAGE_TTL_MS = 7 * 24 * 60 * 60 * 1000;

type PersistedPayload<T> = {
  expiresAt?: number;
  data?: T;
};

export function loadPersistedWorkspaceState<T>(
  storage: Storage = localStorage,
  key = WORKSPACE_STORAGE_KEY,
): T | null {
  const raw = storage.getItem(key);
  if (!raw) return null;

  try {
    const payload = JSON.parse(raw) as PersistedPayload<T>;
    if (
      typeof payload.expiresAt !== "number" ||
      Date.now() > payload.expiresAt ||
      !payload.data ||
      typeof payload.data !== "object"
    ) {
      storage.removeItem(key);
      return null;
    }
    return payload.data;
  } catch {
    storage.removeItem(key);
    return null;
  }
}

export function saveWorkspaceState<T extends object>(
  state: T,
  storage: Storage = localStorage,
  key = WORKSPACE_STORAGE_KEY,
  ttlMs = WORKSPACE_STORAGE_TTL_MS,
): boolean {
  const payload = {
    expiresAt: Date.now() + ttlMs,
    data: state,
  };

  try {
    storage.setItem(key, JSON.stringify(payload));
    return true;
  } catch (err) {
    // Quota exceeded or storage unavailable; persistence is best-effort.
    console.warn("[ImageLab] Could not persist workspace state:", err);
    return false;
  }
}

export function clearPersistedWorkspace(
  storage: Storage = localStorage,
  key = WORKSPACE_STORAGE_KEY,
): void {
  storage.removeItem(key);
}
