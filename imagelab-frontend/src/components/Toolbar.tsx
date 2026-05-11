import { useState, useEffect } from "react";
import * as Blockly from "blockly";
import { FilePlus, Download, Undo2, Redo2, Play, Loader2, Share2, Keyboard } from "lucide-react";
import { usePipelineStore } from "../store/pipelineStore";
import { executePipeline } from "../api/pipeline";
import { extractPipeline } from "../hooks/usePipeline";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";
import SharePipelineModal from "./SharePipelineModal";
import KeyboardShortcutsModal from "./KeyboardShortcutsModal";

interface ToolbarProps {
  workspace: Blockly.WorkspaceSvg | null;
}

// Detect macOS to show Cmd vs Ctrl in tooltips
const isMac =
  typeof navigator !== "undefined" && /mac/i.test(navigator.platform || navigator.userAgent);
const mod = isMac ? "⌘" : "Ctrl+";

export default function Toolbar({ workspace }: ToolbarProps) {
  const {
    originalImage,
    imageFormat,
    processedImage,
    isExecuting,
    setProcessedImage,
    setExecuting,
    setError,
    setTiming,
    reset,
    blockCount,
    uniqueBlockTypes,
    categoryCounts,
    complexity,
  } = usePipelineStore();

  const [showShareModal, setShowShareModal] = useState(false);
  const [showShortcutsModal, setShowShortcutsModal] = useState(false);

  const handleNew = () => {
    if (!window.confirm("This will clear all blocks and the uploaded image. Continue?")) {
      return;
    }
    reset();
    if (workspace) workspace.clear();
  };

  const handleDownload = () => {
    if (!processedImage) return;
    const link = document.createElement("a");
    link.href = `data:image/${imageFormat};base64,${processedImage}`;
    link.download = `processed.${imageFormat}`;
    link.click();
  };

  const handleUndo = () => workspace?.undo(false);
  const handleRedo = () => workspace?.undo(true);

  const handleRun = async () => {
    if (!workspace || !originalImage) return;

    const pipeline = extractPipeline(workspace);
    if (pipeline.length === 0) {
      setError('No pipeline found. Add a "Read Image" block and connect operations.');
      return;
    }

    setExecuting(true);
    setError(null);
    setTiming(null);

    try {
      const response = await executePipeline({
        image: originalImage,
        image_format: imageFormat,
        pipeline,
      });

      setTiming(response.timings ?? null);

      if (response.success && response.image) {
        setProcessedImage(response.image);
      } else {
        setError(response.error || "Pipeline execution failed", response.step);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Network error");
      setTiming(null);
    } finally {
      setExecuting(false);
    }
  };

  // Shift+? opens the shortcuts modal
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "?" && e.shiftKey && !e.ctrlKey && !e.metaKey) {
        const target = e.target as HTMLElement;
        const isEditable =
          target instanceof HTMLInputElement ||
          target instanceof HTMLTextAreaElement ||
          target instanceof HTMLSelectElement ||
          target.isContentEditable;
        if (isEditable) return;
        e.preventDefault();
        setShowShortcutsModal(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Register global keyboard shortcuts
  useKeyboardShortcuts({
    onRun: handleRun,
    onDownload: handleDownload,
    onUndo: handleUndo,
    onRedo: handleRedo,
    workspace,
  });

  const iconBtn =
    "p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 disabled:opacity-40 disabled:cursor-not-allowed transition-colors";
  const separator = "w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1";

  return (
    <>
      <div className="h-10 flex items-center gap-1 px-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <button onClick={handleNew} className={iconBtn} title="New">
          <FilePlus size={18} />
        </button>
        <button
          onClick={handleDownload}
          disabled={!processedImage}
          className={iconBtn}
          title={`Download (${mod}S)`}
        >
          <Download size={18} />
        </button>

        <div className={separator} />

        <button onClick={handleUndo} className={iconBtn} title={`Undo (${mod}Z)`}>
          <Undo2 size={18} />
        </button>
        <button onClick={handleRedo} className={iconBtn} title={`Redo (${mod}Y or ${mod}⇧Z)`}>
          <Redo2 size={18} />
        </button>

        <div className={separator} />

        <button
          onClick={() => setShowShareModal(true)}
          disabled={!workspace}
          className={iconBtn}
          title="Share Pipeline"
        >
          <Share2 size={18} />
        </button>

        <button
          onClick={() => setShowShortcutsModal(true)}
          className={iconBtn}
          title="Keyboard Shortcuts (⇧?)"
        >
          <Keyboard size={18} />
        </button>

        <div className={separator} />

        <button
          onClick={handleRun}
          disabled={isExecuting || !originalImage}
          className="flex items-center gap-1.5 px-3 py-1 rounded-md text-sm font-medium text-white bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title={`Run Pipeline (${mod}Enter)`}
        >
          {isExecuting ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
          {isExecuting ? "Running..." : "Run"}
        </button>

        {/* Spacer to push stats to the right */}
        <div className="flex-1" />

        {/* Live Statistics Display */}
        {blockCount > 0 && (
          <div className="relative group cursor-help px-2 flex items-center h-full border-l border-gray-100 dark:border-gray-700 ml-2">
            <div className="flex flex-col items-end leading-tight">
              <span className="font-semibold text-xs text-gray-700 dark:text-gray-200">
                {blockCount} {blockCount === 1 ? "block" : "blocks"}
              </span>
              <span
                className={`text-[10px] uppercase font-bold tracking-wide ${
                  complexity === "High"
                    ? "text-red-500"
                    : complexity === "Medium"
                      ? "text-orange-500"
                      : "text-green-500"
                }`}
              >
                {complexity} Complexity
              </span>
            </div>

            <div className="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-3 z-50 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200">
              <div className="font-semibold text-xs text-gray-800 dark:text-gray-200 mb-2 border-b border-gray-100 dark:border-gray-700 pb-1.5 uppercase tracking-wider">
                Block Breakdown
              </div>
              <div className="space-y-1.5">
                {Object.entries(categoryCounts)
                  .sort((a, b) => b[1] - a[1])
                  .map(([cat, count]) => (
                    <div
                      key={cat}
                      className="flex justify-between items-center text-xs text-gray-600 dark:text-gray-300"
                    >
                      <span className="truncate pr-2">{cat}</span>
                      <span className="font-medium bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded text-[10px]">
                        {count}
                      </span>
                    </div>
                  ))}
              </div>
              <div className="mt-2.5 pt-2 border-t border-gray-100 dark:border-gray-700 flex justify-between items-center text-gray-500 dark:text-gray-400 text-[10px] uppercase">
                <span>Unique Types</span>
                <span className="font-bold text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">
                  {uniqueBlockTypes}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {showShareModal && (
        <SharePipelineModal workspace={workspace} onClose={() => setShowShareModal(false)} />
      )}

      {showShortcutsModal && (
        <KeyboardShortcutsModal onClose={() => setShowShortcutsModal(false)} />
      )}
    </>
  );
}
