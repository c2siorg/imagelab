import { useState, useEffect, useCallback } from "react";
import * as Blockly from "blockly";
import { X, Loader2, History, RotateCcw } from "lucide-react";
import { usePipelineStore } from "../store/pipelineStore";
import { listVersions, restoreVersion } from "../api/persistence";
import type { VersionSummary } from "../api/persistence";

interface VersionHistoryModalProps {
  workspace: Blockly.WorkspaceSvg | null;
  onClose: () => void;
}

export default function VersionHistoryModal({ workspace, onClose }: VersionHistoryModalProps) {
  const { currentPipelineId, currentPipelineName, setCurrentPipeline, setWorkspaceDirty } =
    usePipelineStore();
  const [versions, setVersions] = useState<VersionSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [restoringId, setRestoringId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchVersions = useCallback(async () => {
    if (!currentPipelineId) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const data = await listVersions(currentPipelineId);
      setVersions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load version history");
    } finally {
      setIsLoading(false);
    }
  }, [currentPipelineId]);

  useEffect(() => {
    void fetchVersions();
  }, [fetchVersions]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const handleRestore = async (version: VersionSummary) => {
    if (!workspace || !currentPipelineId) return;

    if (
      !window.confirm(
        `Are you sure you want to restore Version ${version.version_number}? This will replace your current workspace and create a new version of the pipeline.`,
      )
    ) {
      return;
    }

    setRestoringId(version.id);
    setError(null);

    try {
      const result = await restoreVersion(currentPipelineId, version.version_number);

      // Load workspace state into Blockly
      const snapshot = Blockly.serialization.workspaces.save(workspace);
      workspace.clear();

      try {
        Blockly.serialization.workspaces.load(result.workspace_json, workspace);
      } catch (loadErr) {
        Blockly.serialization.workspaces.load(snapshot, workspace);
        throw loadErr;
      }

      // Reset read-image file label to "No image" if present
      workspace.getBlocksByType("basic_readimage", false).forEach((block) => {
        block.getField("filename_label")?.setValue("No image");
      });

      setCurrentPipeline(currentPipelineId, currentPipelineName, result.version_number);
      setWorkspaceDirty(false);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to restore version");
    } finally {
      setRestoringId(null);
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
        aria-label="Version History"
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden border border-gray-200 dark:border-gray-700 flex flex-col max-h-[80vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 flex-shrink-0">
          <div className="flex items-center gap-2">
            <History size={18} className="text-indigo-500" />
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
              Version History — {currentPipelineName}
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

        {/* Content */}
        <div className="p-5 flex-1 overflow-y-auto space-y-4 min-h-0">
          {error && (
            <div className="p-3 text-xs bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 rounded-lg">
              {error}
            </div>
          )}

          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500">
              <Loader2 size={24} className="animate-spin text-indigo-500 mb-2" />
              <span className="text-xs">Loading version history...</span>
            </div>
          ) : versions.length === 0 ? (
            <div className="text-center py-12 text-gray-400 dark:text-gray-500">
              <span className="text-xs">No version history found.</span>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700 border border-gray-100 dark:border-gray-700 rounded-lg overflow-hidden">
              {versions.map((version) => (
                <div
                  key={version.id}
                  className="flex items-start justify-between p-3.5 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                >
                  <div className="min-w-0 pr-4 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 rounded-md border border-indigo-100/50 dark:border-indigo-900/30">
                        v{version.version_number}
                      </span>
                      <span className="text-[10px] text-gray-400 dark:text-gray-500">
                        {new Date(version.created_at).toLocaleDateString()} at{" "}
                        {new Date(version.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                    <p className="text-xs text-gray-650 dark:text-gray-300 font-medium">
                      {version.change_note || (
                        <span className="italic text-gray-400 dark:text-gray-500">
                          No change note provided
                        </span>
                      )}
                    </p>
                  </div>
                  <div className="flex-shrink-0">
                    <button
                      onClick={() => handleRestore(version)}
                      disabled={restoringId !== null}
                      className="flex items-center gap-1 py-1.5 px-3 rounded-lg text-xs font-medium border border-gray-250 dark:border-gray-600 hover:bg-indigo-50 dark:hover:bg-indigo-950/20 text-gray-600 dark:text-gray-300 hover:text-indigo-500 dark:hover:text-indigo-400 disabled:opacity-50 transition-colors"
                    >
                      {restoringId === version.id ? (
                        <Loader2 size={12} className="animate-spin" />
                      ) : (
                        <RotateCcw size={12} />
                      )}
                      Restore
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
