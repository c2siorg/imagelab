import { useState, useEffect } from "react";
import * as Blockly from "blockly";
import { X, Loader2, Save } from "lucide-react";
import { usePipelineStore } from "../store/pipelineStore";
import { createPipeline, createSharedVersion, createVersion } from "../api/persistence";
import { extractPipeline } from "../hooks/usePipeline";

interface SavePipelineModalProps {
  workspace: Blockly.WorkspaceSvg | null;
  onClose: () => void;
}

export default function SavePipelineModal({ workspace, onClose }: SavePipelineModalProps) {
  const {
    currentPipelineId,
    currentPipelineName,
    currentVersionNumber,
    setCurrentPipeline,
    setWorkspaceDirty,
    shareToken,
  } = usePipelineStore();

  const [name, setName] = useState(currentPipelineName || "");
  const [changeNote, setChangeNote] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const handleSave: React.ComponentProps<"form">["onSubmit"] = async (e) => {
    e.preventDefault();
    if (!workspace) return;

    if (!currentPipelineId && !name.trim()) {
      setError("Pipeline name is required");
      return;
    }

    setIsSaving(true);
    setError(null);

    const workspace_json = Blockly.serialization.workspaces.save(workspace);
    const pipeline_json = { steps: extractPipeline(workspace) };

    try {
      if (currentPipelineId) {
        const payload = {
          workspace_json,
          pipeline_json,
          change_note: changeNote.trim() || undefined,
        };
        const result = shareToken
          ? await createSharedVersion(shareToken, payload)
          : await createVersion(currentPipelineId, payload);
        setCurrentPipeline(result.pipeline_id, currentPipelineName, result.version_number);
        setWorkspaceDirty(false);
      } else {
        const result = await createPipeline({
          name: name.trim(),
          workspace_json,
          pipeline_json,
          change_note: changeNote.trim() || undefined,
        });
        setCurrentPipeline(result.pipeline_id, name.trim(), result.version_number);
        setWorkspaceDirty(false);
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save pipeline");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 backdrop-blur-xs"
      onClick={onClose}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Save Pipeline"
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden border border-gray-200 dark:border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <div className="flex items-center gap-2">
            <Save size={18} className="text-indigo-500" />
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
              {currentPipelineId ? "Save New Version" : "Save Pipeline"}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
            title="Close"
            aria-label="Close"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-5 space-y-4">
          {error && (
            <div className="p-3 text-xs bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 rounded-lg">
              {error}
            </div>
          )}

          {!currentPipelineId ? (
            <div className="space-y-1">
              <label
                htmlFor="pipeline-name"
                className="text-xs font-medium text-gray-600 dark:text-gray-300"
              >
                Pipeline Name
              </label>
              <input
                id="pipeline-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Pipeline"
                className="w-full text-xs bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                required
                disabled={isSaving}
                autoFocus
              />
            </div>
          ) : (
            <div className="p-3 bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/50 rounded-lg">
              <p className="text-xs text-indigo-700 dark:text-indigo-300">
                Saving new version for <span className="font-semibold">{currentPipelineName}</span>.
                This will increment the current version to{" "}
                <span className="font-semibold">v{(currentVersionNumber || 0) + 1}</span>.
              </p>
            </div>
          )}

          <div className="space-y-1">
            <label
              htmlFor="change-note"
              className="text-xs font-medium text-gray-600 dark:text-gray-300"
            >
              Change Note (Optional)
            </label>
            <textarea
              id="change-note"
              value={changeNote}
              onChange={(e) => setChangeNote(e.target.value)}
              placeholder={
                currentPipelineId ? "e.g., Added gaussian blur filter" : "e.g., Initial commit"
              }
              rows={3}
              className="w-full text-xs bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 resize-none"
              disabled={isSaving}
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 px-3 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium text-white bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Saving...
                </>
              ) : (
                "Save"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
