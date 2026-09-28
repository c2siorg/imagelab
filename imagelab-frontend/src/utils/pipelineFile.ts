import * as Blockly from "blockly";
import type { WorkspaceJson } from "../types/blocklyWorkspace";

/** Bump when the exported file layout changes so older or newer files are detectable on import. */
export const PIPELINE_FILE_SCHEMA_VERSION = 1;
export const DEFAULT_PIPELINE_FILE_NAME = "pipeline";

/** Contents of an exported `.json` pipeline file. */
export interface PipelineFile {
  schemaVersion: number;
  name: string;
  workspace: WorkspaceJson;
}

/** Thrown by `parsePipelineFile` with a message that is safe to show to the user. */
export class PipelineFileError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PipelineFileError";
  }
}

export function buildPipelineFile(workspace: Blockly.Workspace, name: string | null): PipelineFile {
  return {
    schemaVersion: PIPELINE_FILE_SCHEMA_VERSION,
    name: name?.trim() || DEFAULT_PIPELINE_FILE_NAME,
    workspace: Blockly.serialization.workspaces.save(workspace),
  };
}

export function serializePipelineFile(file: PipelineFile): string {
  return JSON.stringify(file, null, 2);
}

/** Turns a pipeline name into a safe download filename ending in `.json`. */
export function pipelineFileName(name: string): string {
  const slug = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `${slug || DEFAULT_PIPELINE_FILE_NAME}.json`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Matches the shape `Blockly.serialization.workspaces.save` produces; an empty workspace has no `blocks` key. */
function isWorkspaceJson(value: unknown): value is WorkspaceJson {
  if (!isRecord(value)) return false;
  if (!("blocks" in value)) return true;
  return isRecord(value.blocks) && Array.isArray(value.blocks.blocks);
}

export function parsePipelineFile(text: string): PipelineFile {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new PipelineFileError("The selected file is not valid JSON.");
  }

  if (!isRecord(parsed) || !("schemaVersion" in parsed) || !("workspace" in parsed)) {
    throw new PipelineFileError("The selected file is not an ImageLab pipeline export.");
  }

  if (parsed.schemaVersion !== PIPELINE_FILE_SCHEMA_VERSION) {
    throw new PipelineFileError(
      `Unsupported pipeline file version ${String(parsed.schemaVersion)}. This version of ImageLab reads version ${PIPELINE_FILE_SCHEMA_VERSION}.`,
    );
  }

  if (!isWorkspaceJson(parsed.workspace)) {
    throw new PipelineFileError("The pipeline file does not contain valid workspace data.");
  }

  const name =
    typeof parsed.name === "string" && parsed.name.trim()
      ? parsed.name.trim()
      : DEFAULT_PIPELINE_FILE_NAME;

  return { schemaVersion: PIPELINE_FILE_SCHEMA_VERSION, name, workspace: parsed.workspace };
}

export function readFileText(file: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(typeof reader.result === "string" ? reader.result : "");
    reader.onerror = () => reject(new PipelineFileError("Could not read the selected file."));
    reader.readAsText(file);
  });
}
