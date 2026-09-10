export const WORKSPACE_STORAGE_KEY = "imagelab.pipeline.workspace.v1";
export const ACTIVE_PIPELINE_STORAGE_KEY = "imagelab.pipeline.active.v1";
export const WORKSPACE_STORAGE_TTL_MS = 7 * 24 * 60 * 60 * 1000;

type PersistedPayload<T> = {
  expiresAt?: number;
  data?: T;
};

export interface PersistedActivePipeline {
  id: string;
  name: string;
  versionNumber: number;
}

function loadPersistedPayload<T>(
  storage: Storage,
  key: string,
  isValid: (data: unknown) => data is T,
): T | null {
  const raw = storage.getItem(key);
  if (!raw) return null;

  try {
    const payload = JSON.parse(raw) as PersistedPayload<unknown>;
    if (
      typeof payload.expiresAt !== "number" ||
      Date.now() > payload.expiresAt ||
      !isValid(payload.data)
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

export function loadPersistedWorkspaceState<T>(
  storage: Storage = localStorage,
  key = WORKSPACE_STORAGE_KEY,
): T | null {
  return loadPersistedPayload<T>(
    storage,
    key,
    (data): data is T => Boolean(data) && typeof data === "object",
  );
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

export function loadPersistedActivePipeline(
  storage: Storage = localStorage,
  key = ACTIVE_PIPELINE_STORAGE_KEY,
): PersistedActivePipeline | null {
  return loadPersistedPayload<PersistedActivePipeline>(
    storage,
    key,
    (data): data is PersistedActivePipeline => {
      if (!data || typeof data !== "object") return false;
      const candidate = data as Partial<PersistedActivePipeline>;
      return (
        typeof candidate.id === "string" &&
        candidate.id.length > 0 &&
        typeof candidate.name === "string" &&
        candidate.name.length > 0 &&
        typeof candidate.versionNumber === "number" &&
        Number.isInteger(candidate.versionNumber) &&
        candidate.versionNumber > 0
      );
    },
  );
}

export function saveActivePipeline(
  pipeline: PersistedActivePipeline,
  storage: Storage = localStorage,
  key = ACTIVE_PIPELINE_STORAGE_KEY,
  ttlMs = WORKSPACE_STORAGE_TTL_MS,
): boolean {
  return saveWorkspaceState(pipeline, storage, key, ttlMs);
}

export function clearPersistedActivePipeline(
  storage: Storage = localStorage,
  key = ACTIVE_PIPELINE_STORAGE_KEY,
): void {
  storage.removeItem(key);
}
