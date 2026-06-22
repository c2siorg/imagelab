import { useState, useEffect } from "react";
import * as Blockly from "blockly";
import { X, Loader2, FolderOpen, Trash2, Search } from "lucide-react";
import { usePipelineStore } from "../store/pipelineStore";
import { listPipelines, getPipelineLatest, deletePipeline } from "../api/persistence";
import type { Pipeline } from "../api/persistence";

interface LoadPipelineModalProps {
  workspace: Blockly.WorkspaceSvg | null;
  onClose: () => void;
}

export default function LoadPipelineModal({ workspace, onClose }: LoadPipelineModalProps) {
  const { setCurrentPipeline, setWorkspaceDirty, currentPipelineId } = usePipelineStore();
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchPipelines = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await listPipelines();
      setPipelines(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load pipelines list");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void fetchPipelines();
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const handleLoad = async (pipeline: Pipeline) => {
    if (!workspace) return;

    const existingBlocks = workspace.getAllBlocks(false);
    if (existingBlocks.length > 0) {
      if (!window.confirm("Loading a pipeline will replace your current workspace. Continue?")) {
        return;
      }
    }

    setActionId(pipeline.id);
    setError(null);

    try {
      const latestVersion = await getPipelineLatest(pipeline.id);

      // Load workspace state into Blockly
      const snapshot = Blockly.serialization.workspaces.save(workspace);
      workspace.clear();

      try {
        Blockly.serialization.workspaces.load(latestVersion.workspace_json, workspace);
      } catch (loadErr) {
        // Fallback to snapshot in case of load failure
        Blockly.serialization.workspaces.load(snapshot, workspace);
        throw loadErr;
      }

      // Reset read-image file label to "No image" if present
      workspace.getBlocksByType("basic_readimage", false).forEach((block) => {
        block.getField("filename_label")?.setValue("No image");
      });

      setCurrentPipeline(pipeline.id, pipeline.name, latestVersion.version_number);
      setWorkspaceDirty(false);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load the pipeline configuration");
    } finally {
      setActionId(null);
    }
  };

  const handleDelete = async (pipelineId: string) => {
    if (
      !window.confirm("Are you sure you want to delete this pipeline and all its version history?")
    ) {
      return;
    }

    setActionId(pipelineId);
    setError(null);

    try {
      await deletePipeline(pipelineId);
      setPipelines((prev) => prev.filter((p) => p.id !== pipelineId));
      if (currentPipelineId === pipelineId) {
        setCurrentPipeline(null, null, null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete pipeline");
    } finally {
      setActionId(null);
    }
  };

  const filteredPipelines = pipelines.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 backdrop-blur-xs"
      onClick={onClose}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Load Pipeline"
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden border border-gray-200 dark:border-gray-700 flex flex-col max-h-[80vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 flex-shrink-0">
          <div className="flex items-center gap-2">
            <FolderOpen size={18} className="text-indigo-500" />
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
              Load Pipeline
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

          {/* Search bar */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search pipelines..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            />
          </div>

          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500">
              <Loader2 size={24} className="animate-spin text-indigo-500 mb-2" />
              <span className="text-xs">Loading pipelines...</span>
            </div>
          ) : filteredPipelines.length === 0 ? (
            <div className="text-center py-12 text-gray-400 dark:text-gray-500">
              <span className="text-xs">
                {searchQuery ? "No pipelines match your search." : "No saved pipelines found."}
              </span>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700 border border-gray-100 dark:border-gray-700 rounded-lg overflow-hidden">
              {filteredPipelines.map((pipeline) => (
                <div
                  key={pipeline.id}
                  className="flex items-center justify-between p-3.5 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                >
                  <div className="min-w-0 pr-4">
                    <h3 className="text-xs font-semibold text-gray-800 dark:text-gray-100 truncate">
                      {pipeline.name}
                    </h3>
                    <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">
                      Last updated: {new Date(pipeline.updated_at).toLocaleDateString()} at{" "}
                      {new Date(pipeline.updated_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => handleLoad(pipeline)}
                      disabled={actionId !== null}
                      className="py-1.5 px-3 rounded-lg text-xs font-medium text-white bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 transition-colors shadow-xs"
                    >
                      {actionId === pipeline.id ? (
                        <Loader2 size={12} className="animate-spin" />
                      ) : (
                        "Load"
                      )}
                    </button>
                    <button
                      onClick={() => handleDelete(pipeline.id)}
                      disabled={actionId !== null}
                      className="p-1.5 rounded-lg border border-gray-250 dark:border-gray-600 hover:bg-red-50 dark:hover:bg-red-950/20 text-gray-400 hover:text-red-500 dark:hover:text-red-400 disabled:opacity-50 transition-colors"
                      title="Delete pipeline"
                    >
                      <Trash2 size={14} />
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
