export interface GraphNode {
  id: string;
  type?: string;
  op?: string;
  params?: Record<string, unknown>;
}

export interface GraphEdge {
  from: string;
  to: string;
  input_port?: string | null;
}

export interface PipelineGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  exposed_params?: ExposedParam[];
}

export interface ExposedParam {
  blockId: string;
  blockType: string;
  paramName: string;
  label?: string;
  defaultValue?: unknown;
}

export interface MacroDefinition {
  id: string;
  name: string;
  description?: string | null;
  graph: PipelineGraph;
  exposedParams?: ExposedParam[];
  owner_id?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface MacroItem {
  id: string;
  name: string;
  owner_id?: string | null;
  is_macro: boolean;
  created_at: string;
  updated_at: string;
}

/** The graph JSON returned by the macro API. */
export interface MacroPipelineJson {
  nodes?: GraphNode[];
  edges?: GraphEdge[];
  exposed_params?: ExposedParam[];
}

export interface MacroVersion {
  id: string;
  macro_id: string;
  version_number: number;
  name: string;
  owner_id?: string | null;
  workspace_json: Record<string, unknown>;
  pipeline_json: MacroPipelineJson;
  created_at: string;
  updated_at: string;
}

export interface MacroCreatePayload {
  name: string;
  owner_id?: string | null;
  workspace_json?: Record<string, unknown>;
  pipeline_json: MacroPipelineJson;
  description?: string | null;
}

export interface MacroUpdatePayload {
  name?: string;
  owner_id?: string | null;
  workspace_json?: Record<string, unknown>;
  pipeline_json?: MacroPipelineJson;
  description?: string | null;
}
