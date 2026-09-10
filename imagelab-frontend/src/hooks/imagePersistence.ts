export const IMAGE_STORAGE_KEY = "imagelab.pipeline.image.v1";
export const IMAGE_STORAGE_TTL_MS = 7 * 24 * 60 * 60 * 1000;
const MAX_PERSISTED_IMAGE_CHARS = 3_500_000;

export interface PersistedImageState {
  image: string;
  format: string;
  filename: string | null;
}

type PersistedPayload<T> = {
  expiresAt?: number;
  data?: T;
};

export function loadPersistedImageState(
  storage: Storage = localStorage,
  key = IMAGE_STORAGE_KEY,
): PersistedImageState | null {
  const raw = storage.getItem(key);
  if (!raw) return null;

  try {
    const payload = JSON.parse(raw) as PersistedPayload<PersistedImageState>;
    if (
      typeof payload.expiresAt !== "number" ||
      Date.now() > payload.expiresAt ||
      !payload.data ||
      typeof payload.data.image !== "string" ||
      typeof payload.data.format !== "string" ||
      (payload.data.filename !== null && typeof payload.data.filename !== "string")
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

export function saveImageState(
  state: PersistedImageState,
  storage: Storage = localStorage,
  key = IMAGE_STORAGE_KEY,
  ttlMs = IMAGE_STORAGE_TTL_MS,
): boolean {
  if (state.image.length > MAX_PERSISTED_IMAGE_CHARS) {
    storage.removeItem(key);
    console.warn("[ImageLab] Skipping image persistence because the image is too large.");
    return false;
  }

  const payload = {
    expiresAt: Date.now() + ttlMs,
    data: state,
  };

  try {
    storage.setItem(key, JSON.stringify(payload));
    return true;
  } catch (err) {
    console.warn("[ImageLab] Could not persist image state:", err);
    return false;
  }
}

export function clearPersistedImage(
  storage: Storage = localStorage,
  key = IMAGE_STORAGE_KEY,
): void {
  storage.removeItem(key);
}
