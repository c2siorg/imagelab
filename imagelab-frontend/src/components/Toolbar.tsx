import { useState, useEffect, useCallback } from "react";
import * as Blockly from "blockly";
import {
  FilePlus,
  Download,
  Undo2,
  Redo2,
  Play,
  Loader2,
  Share2,
  Keyboard,
  Save,
  FolderOpen,
  History,
  Layers,
  FolderPlus,
  MousePointer2,
  X,
} from "lucide-react";
import { usePipelineStore } from "../store/pipelineStore";
import { executePipeline, PipelineApiError } from "../api/pipeline";
import { extractExecutableGraph } from "../hooks/usePipeline";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";
import { useStepInspection } from "../hooks/useStepInspection";
import { getSelectedBlocks, getBlocksBetween } from "../utils/extractMacroGraph";
import SharePipelineModal from "./SharePipelineModal";
import KeyboardShortcutsModal from "./KeyboardShortcutsModal";
import SavePipelineModal from "./SavePipelineModal";
import LoadPipelineModal from "./LoadPipelineModal";
import VersionHistoryModal from "./VersionHistoryModal";
import BatchProcessingModal from "./BatchProcessingModal";
import CreateMacroModal from "./modals/CreateMacroModal";

/** Three-phase selection state for 2-click macro range picking. */
type SelectionPhase = "idle" | "selecting" | "waitingForEnd";

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
    setExecutionId,
    setStepResults,
    setActiveStep,
    setActiveStepImage,
    setActiveStepAnalysis,
    setActiveStepHistogram,
    workspaceDirty,
    setWorkspaceDirty,
    setExecuting,
    setError,
    setTiming,
    reset,
    blockCount,
    uniqueBlockTypes,
    categoryCounts,
    complexity,
    currentPipelineId,
    currentPipelineName,
    currentVersionNumber,
    isReadOnly,
    clearShareContext,
  } = usePipelineStore();

  const [showShareModal, setShowShareModal] = useState(false);
  const [showShortcutsModal, setShowShortcutsModal] = useState(false);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showLoadModal, setShowLoadModal] = useState(false);
  const [showVersionModal, setShowVersionModal] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [showCreateMacroModal, setShowCreateMacroModal] = useState(false);

  // ── Fallback single-click selection (used outside range-selection mode) ────
  const [selectedBlocks, setSelectedBlocks] = useState<Blockly.Block[]>([]);

  // ── 2-click range selection state machine ─────────────────────────────────
  const [selectionPhase, setSelectionPhase] = useState<SelectionPhase>("idle");
  const [startBlock, setStartBlock] = useState<Blockly.Block | null>(null);
  const [rangeBlocks, setRangeBlocks] = useState<Blockly.Block[]>([]);
  const [rangeError, setRangeError] = useState<string | null>(null);

  const resetSelectionState = useCallback(() => {
    setSelectionPhase("idle");
    setStartBlock(null);
    setRangeBlocks([]);
    setRangeError(null);
  }, []);

  const inspectStep = useStepInspection();

  // ── Fallback workspace selection listener (active only in idle mode) ───────
  useEffect(() => {
    if (!workspace) {
      setSelectedBlocks([]);
      return;
    }

    const updateSelection = () => {
      const blocks = getSelectedBlocks(workspace);
      setSelectedBlocks(blocks);
    };

    updateSelection();

    const listener = (event: Blockly.Events.Abstract) => {
      if (
        event.type === Blockly.Events.SELECTED ||
        event.type === Blockly.Events.BLOCK_CHANGE ||
        event.type === Blockly.Events.BLOCK_MOVE ||
        event.type === Blockly.Events.BLOCK_CREATE ||
        event.type === Blockly.Events.BLOCK_DELETE
      ) {
        updateSelection();
      }
    };

    workspace.addChangeListener(listener);
    return () => {
      workspace.removeChangeListener(listener);
    };
  }, [workspace]);

  // ── Range selection: workspace CLICK listener ──────────────────────────────
  useEffect(() => {
    if (!workspace || selectionPhase === "idle") return;

    const handleClick = (event: Blockly.Events.Abstract) => {
      // Only respond to block clicks — Blockly.Events.CLICK on a blockId
      if (event.type !== Blockly.Events.CLICK) return;
      const clickEvent = event as Blockly.Events.Click;
      const blockId = clickEvent.blockId;
      if (!blockId) return;

      const clicked = workspace.getBlockById(blockId);
      if (!clicked) return;

      if (selectionPhase === "selecting") {
        // Phase 1 → 2: store start block and provide visual feedback
        setStartBlock(clicked);
        setRangeError(null);
        try {
          clicked.select();
        } catch {
          // select() may not exist in all Blockly versions; safe to ignore
        }
        setSelectionPhase("waitingForEnd");
      } else if (selectionPhase === "waitingForEnd") {
        // Phase 2 → idle: compute range and validate
        if (!startBlock) return;

        if (clicked.id === startBlock.id) {
          // Same block clicked twice — treat as accidental; require a different end block
          setRangeError("Please click a different block as the end block.");
          return;
        }

        try {
          const blocks = getBlocksBetween(startBlock, clicked);
          setRangeBlocks(blocks);
          setRangeError(null);
        } catch (err) {
          setRangeError(err instanceof Error ? err.message : "Invalid block range.");
          setRangeBlocks([]);
        }
        // Return to idle regardless of success/failure — user sees result in toolbar
        setSelectionPhase("idle");
        setStartBlock(null);
      }
    };

    workspace.addChangeListener(handleClick);
    return () => workspace.removeChangeListener(handleClick);
  }, [workspace, selectionPhase, startBlock]);

  const handleNew = () => {
    if (!window.confirm("This will clear all blocks and the uploaded image. Continue?")) {
      return;
    }
    reset();
    clearShareContext();
    if (workspace) {
      workspace.clear();
    }
  };

  const handleDownload = () => {
    if (!processedImage) return;
    const link = document.createElement("a");
    link.href = `data:image/${imageFormat};base64,${processedImage}`;
    link.download = `processed.${imageFormat}`;
    link.click();
  };

  const handleUndo = () => {
    if (!isReadOnly) workspace?.undo(false);
  };
  const handleRedo = () => {
    if (!isReadOnly) workspace?.undo(true);
  };

  const handleRun = async () => {
    if (!workspace || !originalImage) return;

    const graph = extractExecutableGraph(workspace);
    if (graph.nodes.length === 0) {
      setError('No pipeline found. Add a "Read Image" block and connect operations.');
      return;
    }

    setExecuting(true);
    setError(null);
    setTiming(null);
    setExecutionId(null);
    setStepResults([]);
    setActiveStep(null);
    setActiveStepImage(null);
    setActiveStepAnalysis(null);
    setActiveStepHistogram(null);

    try {
      const response = await executePipeline({
        image: originalImage,
        image_format: imageFormat,
        graph,
      });

      setTiming(response.timings ?? null);
      setExecutionId(response.execution_id ?? null);
      setStepResults(response.step_results ?? []);

      if (response.success && response.image) {
        setProcessedImage(response.image);
        const lastStep = response.step_results?.filter((step) => step.success).at(-1);
        if (lastStep) {
          await inspectStep(lastStep, { clearAnalysis: false });
        } else {
          setActiveStep(null);
        }
        setWorkspaceDirty(false);
      } else {
        setError(response.error || "Pipeline execution failed", response.step);
        const lastStep = response.step_results?.filter((step) => step.success).at(-1);
        if (lastStep) {
          await inspectStep(lastStep, { clearAnalysis: false });
        }
      }
    } catch (err) {
      if (err instanceof PipelineApiError) {
        setError(`Step execution failed in ${err.detail.step_type}: ${err.detail.message}`);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Network error");
      }
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

  // Determine which blocks feed the Create Macro modal
  const macroSourceBlocks = rangeBlocks.length >= 2 ? rangeBlocks : selectedBlocks;
  const canCreateMacro = macroSourceBlocks.length >= 2 && !isReadOnly;

  // Phase-specific banner labels
  const phaseBannerText =
    selectionPhase === "selecting"
      ? "Click the START block on the canvas…"
      : selectionPhase === "waitingForEnd"
        ? "Now click the END block…"
        : null;

  return (
    <>
      {/* Selection mode banner */}
      {(selectionPhase !== "idle" || rangeError) && (
        <div
          className={`px-4 py-1 text-xs flex items-center gap-2 border-b ${
            rangeError
              ? "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400"
              : "bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900/40 text-amber-700 dark:text-amber-300"
          }`}
        >
          <MousePointer2 size={12} className="shrink-0" />
          <span className="flex-1">{rangeError ?? phaseBannerText}</span>
          {rangeError && (
            <button
              type="button"
              onClick={() => setRangeError(null)}
              className="ml-auto p-0.5 rounded hover:bg-red-100 dark:hover:bg-red-900/40"
              title="Dismiss"
              aria-label="Dismiss range error"
            >
              <X size={11} />
            </button>
          )}
        </div>
      )}
      <div className="h-10 flex items-center gap-1 px-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <button onClick={handleNew} disabled={isReadOnly} className={iconBtn} title="New">
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

        <button
          onClick={() => setShowSaveModal(true)}
          disabled={!workspace || isReadOnly}
          className={`${iconBtn} relative`}
          title="Save Pipeline"
        >
          <Save size={18} />
          {workspaceDirty && (
            <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-indigo-500 rounded-full" />
          )}
        </button>
        <button
          onClick={() => setShowLoadModal(true)}
          disabled={!workspace || isReadOnly}
          className={iconBtn}
          title="Load Pipeline"
        >
          <FolderOpen size={18} />
        </button>
        <button
          onClick={() => setShowVersionModal(true)}
          disabled={!currentPipelineId || isReadOnly}
          className={iconBtn}
          title="Version History"
        >
          <History size={18} />
        </button>

        {currentPipelineId && (
          <>
            <div className={separator} />
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-gray-50 dark:bg-gray-700/50 border border-gray-150 dark:border-gray-700">
              <span className="text-[11px] font-semibold text-gray-750 dark:text-gray-250 truncate max-w-[120px]">
                {currentPipelineName}
              </span>
              <span className="text-[9px] px-1.5 py-0.2 rounded font-extrabold bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300">
                v{currentVersionNumber}
              </span>
              {workspaceDirty && (
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500" title="Unsaved changes" />
              )}
            </div>
          </>
        )}

        <div className={separator} />

        <button
          onClick={handleUndo}
          disabled={isReadOnly}
          className={iconBtn}
          title={`Undo (${mod}Z)`}
        >
          <Undo2 size={18} />
        </button>
        <button
          onClick={handleRedo}
          disabled={isReadOnly}
          className={iconBtn}
          title={`Redo (${mod}Y or ${mod}⇧Z)`}
        >
          <Redo2 size={18} />
        </button>

        <div className={separator} />

        <button
          onClick={() => setShowShareModal(true)}
          disabled={!workspace || isReadOnly}
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
          onClick={() => setShowBatchModal(true)}
          disabled={isExecuting || blockCount === 0 || isReadOnly}
          className="flex items-center gap-1.5 px-3 py-1 rounded-md text-sm font-medium text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800 hover:bg-indigo-50 dark:hover:bg-indigo-950/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Batch Run"
        >
          <Layers size={16} />
          Batch Run
        </button>

        {/* ── Macro range selection controls ─────────────────────────────── */}
        <div className={separator} />

        {/* "Select Macro Range" toggle button */}
        {selectionPhase === "idle" ? (
          <button
            id="btn-select-macro-range"
            onClick={() => {
              setRangeBlocks([]);
              setRangeError(null);
              setSelectionPhase("selecting");
            }}
            disabled={isReadOnly || blockCount === 0}
            className="flex items-center gap-1.5 px-3 py-1 rounded-md text-sm font-medium text-violet-600 dark:text-violet-400 border border-violet-200 dark:border-violet-800 hover:bg-violet-50 dark:hover:bg-violet-950/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="2-click range selection: click start block then end block"
          >
            <MousePointer2 size={16} />
            Select Range
          </button>
        ) : (
          <button
            id="btn-cancel-macro-selection"
            onClick={resetSelectionState}
            className="flex items-center gap-1.5 px-3 py-1 rounded-md text-sm font-medium text-orange-600 dark:text-orange-400 border border-orange-300 dark:border-orange-700 bg-orange-50 dark:bg-orange-950/30 hover:bg-orange-100 dark:hover:bg-orange-950/50 animate-pulse transition-colors"
            title="Cancel range selection"
          >
            <X size={16} />
            Cancel Selection
          </button>
        )}

        <button
          id="btn-create-macro"
          onClick={() => setShowCreateMacroModal(true)}
          disabled={!canCreateMacro}
          className="flex items-center gap-1.5 px-3 py-1 rounded-md text-sm font-medium text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title={
            rangeBlocks.length >= 2
              ? `Create macro from ${rangeBlocks.length} selected blocks`
              : "Create Macro from selected workspace blocks"
          }
        >
          <FolderPlus size={16} />
          Create Macro
        </button>

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
        <SharePipelineModal
          workspace={workspace}
          onClose={() => setShowShareModal(false)}
          onSaveFirst={() => setShowSaveModal(true)}
        />
      )}

      {showShortcutsModal && (
        <KeyboardShortcutsModal onClose={() => setShowShortcutsModal(false)} />
      )}

      {showSaveModal && (
        <SavePipelineModal workspace={workspace} onClose={() => setShowSaveModal(false)} />
      )}

      {showLoadModal && (
        <LoadPipelineModal workspace={workspace} onClose={() => setShowLoadModal(false)} />
      )}

      {showVersionModal && (
        <VersionHistoryModal workspace={workspace} onClose={() => setShowVersionModal(false)} />
      )}

      {showBatchModal && workspace && (
        <BatchProcessingModal
          graph={extractExecutableGraph(workspace)}
          onClose={() => setShowBatchModal(false)}
        />
      )}

      {showCreateMacroModal && (
        <CreateMacroModal
          selectedBlocks={macroSourceBlocks}
          onClose={() => {
            setShowCreateMacroModal(false);
            // Clear range blocks after modal closes so the button goes back to disabled
            setRangeBlocks([]);
          }}
        />
      )}
    </>
  );
}
