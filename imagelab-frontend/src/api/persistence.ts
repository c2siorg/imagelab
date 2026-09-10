import type { WorkspaceJson } from "../types/blocklyWorkspace";
import type { PersistedPipelineJson } from "../types/pipeline";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4100";

export interface Pipeline {
  id: string;
  name: string;
  owner_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface PipelineVersion {
  id: string;
  pipeline_id: string;
  version_number: number;
  workspace_json: WorkspaceJson;
  pipeline_json: PersistedPipelineJson;
  change_note: string | null;
  created_at: string;
}

export interface VersionSummary {
  id: string;
  pipeline_id: string;
  version_number: number;
  change_note: string | null;
  created_at: string;
}

export interface SharedPipeline {
  pipeline_id: string;
  pipeline_name: string;
  version_number: number;
  workspace_json: WorkspaceJson;
  pipeline_json: PersistedPipelineJson;
  permission: "view" | "clone" | "edit";
}

// API functions
function formatApiError(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e) => (typeof e === "object" && e && "msg" in e ? String(e.msg) : String(e)))
      .join("; ");
  }
  return fallback;
}

export async function createPipeline(payload: {
  name: string;
  workspace_json: WorkspaceJson;
  pipeline_json: PersistedPipelineJson;
  change_note?: string;
  owner_id?: string;
}): Promise<PipelineVersion> {
  const response = await fetch(`${API_URL}/api/pipelines/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(formatApiError(errorData.detail, "Failed to create pipeline"));
  }
  return response.json();
}

export async function listPipelines(): Promise<Pipeline[]> {
  const response = await fetch(`${API_URL}/api/pipelines/`);
  if (!response.ok) {
    throw new Error("Failed to list pipelines");
  }
  return response.json();
}

export async function getPipelineLatest(pipelineId: string): Promise<PipelineVersion> {
  const response = await fetch(`${API_URL}/api/pipelines/${pipelineId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch pipeline");
  }
  return response.json();
}

export async function deletePipeline(pipelineId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/pipelines/${pipelineId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Failed to delete pipeline");
  }
}

export async function createVersion(
  pipelineId: string,
  payload: {
    workspace_json: WorkspaceJson;
    pipeline_json: PersistedPipelineJson;
    change_note?: string;
  },
): Promise<PipelineVersion> {
  const response = await fetch(`${API_URL}/api/pipelines/${pipelineId}/versions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(formatApiError(errorData.detail, "Failed to create new version"));
  }
  return response.json();
}

export async function listVersions(pipelineId: string): Promise<VersionSummary[]> {
  const response = await fetch(`${API_URL}/api/pipelines/${pipelineId}/versions`);
  if (!response.ok) {
    throw new Error("Failed to list versions");
  }
  return response.json();
}

export async function getVersion(
  pipelineId: string,
  versionNumber: number,
): Promise<PipelineVersion> {
  const response = await fetch(`${API_URL}/api/pipelines/${pipelineId}/versions/${versionNumber}`);
  if (!response.ok) {
    throw new Error("Failed to fetch version");
  }
  return response.json();
}

export async function restoreVersion(
  pipelineId: string,
  versionNumber: number,
): Promise<PipelineVersion> {
  const response = await fetch(`${API_URL}/api/pipelines/${pipelineId}/restore/${versionNumber}`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Failed to restore version");
  }
  return response.json();
}

// Sharing API functions
export async function createShareToken(
  pipelineId: string,
  payload: {
    version_number: number;
    permission: "view" | "clone" | "edit";
    expires_at?: string; // ISO string
  },
): Promise<{ token: string }> {
  const response = await fetch(`${API_URL}/api/pipelines/${pipelineId}/share`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to generate share link");
  }
  return response.json();
}

export async function lookupShareToken(token: string): Promise<SharedPipeline> {
  const response = await fetch(`${API_URL}/api/share/${token}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Invalid or expired share link");
  }
  return response.json();
}

export async function cloneShareToken(
  token: string,
  payload?: { name?: string; owner_id?: string },
): Promise<PipelineVersion> {
  const response = await fetch(`${API_URL}/api/share/${token}/clone`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to clone shared pipeline");
  }
  return response.json();
}

export async function createSharedVersion(
  token: string,
  payload: {
    workspace_json: WorkspaceJson;
    pipeline_json: PersistedPipelineJson;
    change_note?: string;
  },
): Promise<PipelineVersion> {
  const response = await fetch(`${API_URL}/api/share/${token}/versions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(formatApiError(errorData.detail, "Failed to save shared pipeline version"));
  }
  return response.json();
}
