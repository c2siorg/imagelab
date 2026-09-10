import type { MacroCreatePayload, MacroUpdatePayload, MacroVersion } from "../types/macro";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4100";

export async function fetchMacros(): Promise<MacroVersion[]> {
  const response = await fetch(`${API_URL}/api/v1/macros`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch macros (status ${response.status})`);
  }
  return response.json();
}

export async function createMacro(payload: MacroCreatePayload): Promise<MacroVersion> {
  const response = await fetch(`${API_URL}/api/v1/macros`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to create macro (status ${response.status})`);
  }
  return response.json();
}

export async function getMacro(macroId: string): Promise<MacroVersion> {
  const response = await fetch(`${API_URL}/api/v1/macros/${encodeURIComponent(macroId)}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    throw new Error(`Failed to retrieve macro ${macroId} (status ${response.status})`);
  }
  return response.json();
}

export async function updateMacro(
  macroId: string,
  payload: MacroUpdatePayload,
): Promise<MacroVersion> {
  const response = await fetch(`${API_URL}/api/v1/macros/${encodeURIComponent(macroId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to update macro (status ${response.status})`);
  }
  return response.json();
}

export async function deleteMacro(macroId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/macros/${encodeURIComponent(macroId)}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to delete macro (status ${response.status})`);
  }
}
