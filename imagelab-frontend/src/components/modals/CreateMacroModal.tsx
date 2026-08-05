import { useEffect, useMemo, useState } from "react";
import * as Blockly from "blockly";
import { FolderPlus, Loader2, X } from "lucide-react";
import { useMacroStore } from "../../store/useMacroStore";
import type { ExposedParam } from "../../types/macro";
import { extractExposedParamCandidates, extractMacroGraph } from "../../utils/extractMacroGraph";

interface CreateMacroModalProps {
  selectedBlocks: Blockly.Block[];
  onClose: () => void;
}

export default function CreateMacroModal({ selectedBlocks, onClose }: CreateMacroModalProps) {
  const addMacro = useMacroStore((state) => state.addMacro);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Extract graph & exposed param candidates on mount / block change
  const { graph, candidates, initError } = useMemo(() => {
    try {
      const g = extractMacroGraph(selectedBlocks);
      const c = extractExposedParamCandidates(selectedBlocks);
      return { graph: g, candidates: c, initError: null };
    } catch (err) {
      return {
        graph: null,
        candidates: [],
        initError:
          err instanceof Error ? err.message : "Failed to extract macro graph from selection",
      };
    }
  }, [selectedBlocks]);

  // Track which parameters are selected to be exposed (default all checked)
  const [exposedSelection, setExposedSelection] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    candidates.forEach((c) => {
      initial[`${c.blockId}:${c.paramName}`] = true;
    });
    return initial;
  });

  useEffect(() => {
    if (initError) {
      setError(initError);
    }
  }, [initError]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const toggleParam = (key: string) => {
    setExposedSelection((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleSubmit: React.ComponentProps<"form">["onSubmit"] = async (e) => {
    e.preventDefault();
    if (!graph) return;

    if (!name.trim()) {
      setError("Macro name is required");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    const exposedParams: ExposedParam[] = candidates.filter(
      (c) => exposedSelection[`${c.blockId}:${c.paramName}`],
    );

    const pipeline_json = {
      nodes: graph.nodes,
      edges: graph.edges,
      exposed_params: exposedParams,
    };

    const workspace_json: Record<string, unknown> = {
      block_ids: selectedBlocks.map((b) => b.id),
    };

    try {
      await addMacro({
        name: name.trim(),
        description: description.trim() || undefined,
        pipeline_json,
        workspace_json,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create macro");
    } finally {
      setIsSubmitting(false);
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
        aria-label="Create Macro"
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden border border-gray-200 dark:border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <div className="flex items-center gap-2">
            <FolderPlus size={18} className="text-indigo-500" />
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
              Create New Macro
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

        <form onSubmit={handleSubmit} className="p-5 space-y-4 max-h-[80vh] overflow-y-auto">
          {error && (
            <div
              data-testid="error-banner"
              className="p-3 text-xs bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 rounded-lg"
            >
              {error}
            </div>
          )}

          <div className="space-y-1">
            <label
              htmlFor="macro-name"
              className="text-xs font-medium text-gray-600 dark:text-gray-300"
            >
              Macro Name *
            </label>
            <input
              id="macro-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Edge Detection Blur"
              className="w-full text-xs bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
              required
              disabled={isSubmitting || Boolean(initError)}
              autoFocus
            />
          </div>

          <div className="space-y-1">
            <label
              htmlFor="macro-description"
              className="text-xs font-medium text-gray-600 dark:text-gray-300"
            >
              Description (Optional)
            </label>
            <textarea
              id="macro-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Combines gaussian blur with Canny edge detection"
              rows={2}
              className="w-full text-xs bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 resize-none"
              disabled={isSubmitting || Boolean(initError)}
            />
          </div>

          {/* Exposed Parameters Checklist */}
          {candidates.length > 0 && (
            <div className="space-y-2 pt-1 border-t border-gray-100 dark:border-gray-700">
              <label className="text-xs font-medium text-gray-600 dark:text-gray-300 flex justify-between items-center">
                <span>Exposed Parameters</span>
                <span className="text-[10px] text-gray-400 font-normal">
                  Select parameters to expose
                </span>
              </label>
              <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                {candidates.map((c) => {
                  const key = `${c.blockId}:${c.paramName}`;
                  const isChecked = Boolean(exposedSelection[key]);
                  return (
                    <label
                      key={key}
                      htmlFor={`param-${key}`}
                      className="flex items-center gap-2 px-2.5 py-1.5 rounded bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <input
                        id={`param-${key}`}
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggleParam(key)}
                        disabled={isSubmitting || Boolean(initError)}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5"
                      />
                      <div className="flex-1 flex justify-between items-center text-xs">
                        <span className="font-medium text-gray-700 dark:text-gray-200">
                          {c.paramName}
                        </span>
                        <span className="text-[10px] text-gray-400 font-mono">{c.blockType}</span>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 px-3 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium text-white bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
              disabled={isSubmitting || Boolean(initError)}
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Macro"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
