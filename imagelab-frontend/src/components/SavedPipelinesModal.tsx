import { useState, useEffect } from "react";
import * as Blockly from "blockly";
import { X, Save, FolderOpen, Trash2, Download, Loader2 } from "lucide-react";
import { savePipeline, listPipelines, getPipeline, deletePipeline } from "../api/savedPipelines";
import { extractPipeline } from "../hooks/usePipeline";
import type { SavedPipelineSummary } from "../types/pipeline";

const READ_IMAGE_BLOCK_TYPE = "basic_readimage";
const FILENAME_LABEL_FIELD = "filename_label";

interface SavedPipelinesModalProps {
  workspace: Blockly.WorkspaceSvg | null;
  onClose: () => void;
}

type Tab = "save" | "load";

export default function SavedPipelinesModal({ workspace, onClose }: SavedPipelinesModalProps) {
  const [tab, setTab] = useState<Tab>("save");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const [pipelines, setPipelines] = useState<SavedPipelineSummary[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  useEffect(() => {
    if (tab === "load") {
      setLoadingList(true);
      listPipelines()
        .then(setPipelines)
        .catch(() => setLoadError("Failed to load pipelines"))
        .finally(() => setLoadingList(false));
    }
  }, [tab]);

  const handleSave = async () => {
    if (!workspace || !name.trim()) return;
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      const pipeline = extractPipeline(workspace);
      const workspaceState = JSON.stringify(Blockly.serialization.workspaces.save(workspace));
      await savePipeline({
        name: name.trim(),
        description: description.trim(),
        pipeline_json: JSON.stringify(pipeline),
        workspace_state: workspaceState,
      });
      setSaveSuccess(true);
      setTimeout(() => onClose(), 1000);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleLoad = async (id: number) => {
    if (!workspace) return;
    setLoadError(null);
    try {
      const saved = await getPipeline(id);
      const existingBlocks = workspace.getAllBlocks(false);
      if (existingBlocks.length > 0) {
        if (!window.confirm("Loading will replace your current workspace. Continue?")) return;
      }
      const snapshot = Blockly.serialization.workspaces.save(workspace);
      workspace.clear();
      try {
        if (saved.workspace_state) {
          Blockly.serialization.workspaces.load(
            JSON.parse(saved.workspace_state) as Parameters<
              typeof Blockly.serialization.workspaces.load
            >[0],
            workspace,
          );
        }
      } catch {
        Blockly.serialization.workspaces.load(snapshot, workspace);
        setLoadError("Failed to restore workspace state");
        return;
      }
      workspace.getBlocksByType(READ_IMAGE_BLOCK_TYPE, false).forEach((block) => {
        block.getField(FILENAME_LABEL_FIELD)?.setValue("No image");
      });
      onClose();
    } catch {
      setLoadError("Failed to load pipeline");
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Delete this pipeline?")) return;
    setDeletingId(id);
    try {
      await deletePipeline(id);
      setPipelines((prev) => prev.filter((p) => p.id !== id));
    } catch {
      setLoadError("Failed to delete pipeline");
    } finally {
      setDeletingId(null);
    }
  };

  const tabBtn = (t: Tab) =>
    `flex-1 py-2 text-xs font-semibold border-b-2 transition-colors ${
      tab === t
        ? "border-indigo-500 text-indigo-600"
        : "border-transparent text-gray-500 hover:text-gray-700"
    }`;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={onClose}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Saved Pipelines"
        className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <FolderOpen size={18} className="text-indigo-500" />
            <h2 className="text-sm font-semibold text-gray-800">Saved Pipelines</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded hover:bg-gray-100 text-gray-400"
          >
            <X size={16} />
          </button>
        </div>

        <div className="flex border-b border-gray-100">
          <button type="button" className={tabBtn("save")} onClick={() => setTab("save")}>
            Save Current
          </button>
          <button type="button" className={tabBtn("load")} onClick={() => setTab("load")}>
            My Pipelines
          </button>
        </div>

        <div className="p-5">
          {tab === "save" && (
            <div className="space-y-3">
              <input
                type="text"
                placeholder="Pipeline name *"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
              <textarea
                placeholder="Description (optional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
              />
              {saveError && <p className="text-xs text-red-500">{saveError}</p>}
              {saveSuccess && <p className="text-xs text-green-600">Saved successfully!</p>}
              <button
                type="button"
                onClick={handleSave}
                disabled={saving || !name.trim() || !workspace}
                className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium text-white bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                {saving ? "Saving..." : "Save Pipeline"}
              </button>
            </div>
          )}

          {tab === "load" && (
            <div className="space-y-2 max-h-72 overflow-y-auto">
              {loadingList && (
                <div className="flex items-center justify-center py-6">
                  <Loader2 size={18} className="animate-spin text-indigo-400" />
                </div>
              )}
              {loadError && <p className="text-xs text-red-500">{loadError}</p>}
              {!loadingList && pipelines.length === 0 && (
                <p className="text-xs text-gray-400 text-center py-6">No saved pipelines yet.</p>
              )}
              {pipelines.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center gap-2 p-2.5 rounded-lg border border-gray-100 hover:bg-gray-50"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-700 truncate">{p.name}</p>
                    {p.description && (
                      <p className="text-xs text-gray-400 truncate">{p.description}</p>
                    )}
                    <p className="text-[10px] text-gray-300 mt-0.5">
                      {new Date(p.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleLoad(p.id)}
                    className="p-1.5 rounded hover:bg-indigo-50 text-indigo-500 transition-colors"
                    title="Load pipeline"
                  >
                    <Download size={14} />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(p.id)}
                    disabled={deletingId === p.id}
                    className="p-1.5 rounded hover:bg-red-50 text-red-400 transition-colors disabled:opacity-40"
                    title="Delete pipeline"
                  >
                    {deletingId === p.id ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <Trash2 size={14} />
                    )}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
