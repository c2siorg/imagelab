import { useEffect, useState } from "react";
import * as Blockly from "blockly";
import { X, Loader2, Copy } from "lucide-react";
import { cloneShareToken } from "../api/persistence";
import type { SharedPipeline } from "../api/persistence";
import { loadWorkspaceState } from "../utils/workspaceLoad";

interface CloneSharedPipelineModalProps {
  workspace: Blockly.WorkspaceSvg;
  shareToken: string;
  sharedPipeline: SharedPipeline;
  onComplete: (pipelineId: string, name: string) => void;
  onCancel: () => void;
}

export default function CloneSharedPipelineModal({
  workspace,
  shareToken,
  sharedPipeline,
  onComplete,
  onCancel,
}: CloneSharedPipelineModalProps) {
  const [name, setName] = useState(`Clone of ${sharedPipeline.pipeline_name}`);
  const [isCloning, setIsCloning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onCancel]);

  const handleClone: React.ComponentProps<"form">["onSubmit"] = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Pipeline name is required");
      return;
    }

    setIsCloning(true);
    setError(null);

    try {
      const cloned = await cloneShareToken(shareToken, { name: name.trim() });
      loadWorkspaceState(workspace, cloned.workspace_json);
      onComplete(cloned.pipeline_id, name.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to clone shared pipeline");
    } finally {
      setIsCloning(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 backdrop-blur-xs"
      onClick={onCancel}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Clone Shared Pipeline"
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden border border-gray-200 dark:border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <div className="flex items-center gap-2">
            <Copy size={18} className="text-indigo-500" />
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
              Clone Shared Pipeline
            </h2>
          </div>
          <button
            type="button"
            onClick={onCancel}
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
            title="Close"
            aria-label="Close"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>

        <form onSubmit={handleClone} className="p-5 space-y-4">
          <p className="text-xs text-gray-600 dark:text-gray-300">
            You received a clone link for{" "}
            <span className="font-semibold">{sharedPipeline.pipeline_name}</span> (v
            {sharedPipeline.version_number}). Name your copy to start editing independently.
          </p>

          {error && (
            <div className="p-3 text-xs bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 rounded-lg">
              {error}
            </div>
          )}

          <div className="space-y-1">
            <label
              htmlFor="clone-pipeline-name"
              className="text-xs font-medium text-gray-600 dark:text-gray-300"
            >
              New Pipeline Name
            </label>
            <input
              id="clone-pipeline-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full text-xs bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
              disabled={isCloning}
              autoFocus
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 py-2 px-3 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              disabled={isCloning}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium text-white bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
              disabled={isCloning}
            >
              {isCloning ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Cloning...
                </>
              ) : (
                "Clone Pipeline"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
