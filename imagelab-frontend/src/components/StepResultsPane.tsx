import { useEffect, useMemo, useRef, useState } from "react";
import * as Blockly from "blockly";
import { ChevronDown, ChevronRight, ImageDown, Loader2, RefreshCw } from "lucide-react";
import { executePipeline } from "../api/pipeline";
import { extractExecutablePipeline } from "../hooks/usePipeline";
import { useStepInspection } from "../hooks/useStepInspection";
import { usePipelineStore } from "../store/pipelineStore";
import { useMacroStore } from "../store/useMacroStore";
import type { StepResult } from "../types/pipeline";
import ImageModal from "./Preview/ImageModal";

interface StepResultsPaneProps {
  workspace: Blockly.WorkspaceSvg | null;
}

function getStepLabel(operatorType: string): string {
  const underscoreIndex = operatorType.indexOf("_");
  return underscoreIndex !== -1 ? operatorType.slice(underscoreIndex + 1) : operatorType;
}

function getCardKey(step: StepResult): string {
  return step.block_id ?? String(step.index);
}

function getMacroParentId(
  blockId: string | undefined,
  workspace: Blockly.WorkspaceSvg | null,
): string | null {
  if (!blockId || !workspace) return null;

  const colonIndex = blockId.indexOf(":");
  if (colonIndex === -1) return null;

  const candidateParentId = blockId.slice(0, colonIndex);
  const parentBlock = workspace.getBlockById(candidateParentId);
  if (parentBlock && (parentBlock.type.startsWith("macro_") || "macroName" in parentBlock)) {
    return candidateParentId;
  }

  // Not a macro step — just a standard block whose random ID contained a colon!
  return null;
}

type InlineItem =
  | { kind: "step"; step: StepResult }
  | { kind: "macro"; macroBlockId: string; steps: StepResult[] };

/**
 * Groups step results into a single horizontal sequence.
 * Macro internal steps get grouped under their parent macro block ID
 * and placed inline at the exact spot where the macro executed.
 */
function organizeStepsInline(
  steps: StepResult[],
  workspace: Blockly.WorkspaceSvg | null,
): InlineItem[] {
  const items: InlineItem[] = [];
  const processedMacros = new Map<string, StepResult[]>();

  for (const step of steps) {
    const parentId = getMacroParentId(step.block_id || "", workspace);

    if (parentId) {
      if (!processedMacros.has(parentId)) {
        const group: StepResult[] = [];
        processedMacros.set(parentId, group);
        items.push({ kind: "macro", macroBlockId: parentId, steps: group });
      }
      processedMacros.get(parentId)!.push(step);
    } else {
      items.push({ kind: "step", step });
    }
  }

  return items;
}
export default function StepResultsPane({ workspace }: StepResultsPaneProps) {
  const {
    originalImage,
    imageFormat,
    stepResults,
    activeStepBlockId,
    activeStepIndex,
    isInspectingStep,
    isExecuting,
    workspaceDirty,
    setProcessedImage,
    setExecutionId,
    setStepResults,
    setActiveStep,
    setActiveStepImage,
    setActiveStepAnalysis,
    setActiveStepHistogram,
    setExecuting,
    setError,
    setTiming,
    setWorkspaceDirty,
  } = usePipelineStore();
  const { macros } = useMacroStore();
  const cardRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const clickTimeoutRef = useRef<number | null>(null);
  const [modalImageSrc, setModalImageSrc] = useState<string | null>(null);
  const [collapsedMacros, setCollapsedMacros] = useState<Set<string>>(new Set());
  const inspectStep = useStepInspection();

  // Organize steps inline horizontally
  const inlineItems = useMemo(
    () => organizeStepsInline(stepResults, workspace),
    [stepResults, workspace],
  );

  const finalStep = useMemo(
    () => [...stepResults].reverse().find((step) => step.success),
    [stepResults],
  );

  const activeMacroBlockIds = useMemo(() => {
    return inlineItems
      .filter((item): item is Extract<InlineItem, { kind: "macro" }> => item.kind === "macro")
      .map((item) => item.macroBlockId);
  }, [inlineItems]);

  useEffect(() => {
    const activeKey =
      activeStepBlockId ?? (activeStepIndex !== null ? String(activeStepIndex) : null);
    if (!activeKey) return;
    cardRefs.current[activeKey]?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
      inline: "center",
    });
  }, [activeStepBlockId, activeStepIndex]);

  useEffect(() => {
    return () => {
      if (clickTimeoutRef.current !== null) {
        window.clearTimeout(clickTimeoutRef.current);
      }
    };
  }, []);

  // Initialize all detected macro blocks as collapsed by default
  useEffect(() => {
    setCollapsedMacros((prev) => {
      const next = new Set(prev);
      for (const id of activeMacroBlockIds) {
        if (!next.has(id)) {
          next.add(id); // Default to collapsed
        }
      }
      return next;
    });
  }, [activeMacroBlockIds]);

  const toggleMacroCollapse = (macroBlockId: string) => {
    setCollapsedMacros((prev) => {
      const next = new Set(prev);
      if (next.has(macroBlockId)) {
        next.delete(macroBlockId);
      } else {
        next.add(macroBlockId);
      }
      return next;
    });
  };

  // Resolves the block instance back to its Macro template name on the canvas
  const getMacroDisplayName = (macroBlockId: string): string => {
    let resolvedName = "Macro";

    if (workspace) {
      const block = workspace.getBlockById(macroBlockId);
      if (block) {
        const displayTitle =
          block.getFieldValue("TITLE") ||
          block.getFieldValue("MACRO_TITLE") ||
          (block as unknown as { macroName?: string }).macroName;

        if (
          displayTitle &&
          typeof displayTitle === "string" &&
          !displayTitle.startsWith("macro_")
        ) {
          resolvedName = displayTitle;
        } else if (block.type.startsWith("macro_")) {
          const rawId = block.type.replace(/^macro_/, "");
          const matched = macros.find((m) => m.id === rawId);
          if (matched) {
            resolvedName = matched.name;
          } else {
            resolvedName = "Nested Macro";
          }
        } else {
          // Standard block fallback
          resolvedName = block.type
            .replace(
              /^(geometric_|filtering_|morphological_|color_|edge_|transform_|drawing_|basic_|op_)/,
              "",
            )
            .replace(/_+/g, " ")
            .replace(/\b\w/g, (l) => l.toUpperCase());
        }
        return resolvedName;
      }
    }
    return resolvedName;
  };
  const selectWorkspaceBlock = (step: StepResult) => {
    if (step.block_id && workspace) {
      const block = workspace.getBlockById(step.block_id);
      if (block) {
        workspace.centerOnBlock(step.block_id);
        Blockly.common.setSelected(block);
      }
    }
  };

  const handleStepClick = async (step: StepResult) => {
    const inspection = inspectStep(step);
    selectWorkspaceBlock(step);
    await inspection;
  };

  const handleStepDoubleClick = async (step: StepResult) => {
    const inspection = inspectStep(step);
    selectWorkspaceBlock(step);
    const inspected = await inspection;
    if (inspected) {
      setModalImageSrc(`data:image/${inspected.image_format};base64,${inspected.image}`);
    }
  };

  const handleCardClick = (step: StepResult) => {
    if (clickTimeoutRef.current !== null) {
      window.clearTimeout(clickTimeoutRef.current);
    }
    clickTimeoutRef.current = window.setTimeout(() => {
      void handleStepClick(step);
      clickTimeoutRef.current = null;
    }, 220);
  };

  const handleCardDoubleClick = (step: StepResult) => {
    if (clickTimeoutRef.current !== null) {
      window.clearTimeout(clickTimeoutRef.current);
      clickTimeoutRef.current = null;
    }
    void handleStepDoubleClick(step);
  };

  const handleRefresh = async () => {
    if (!workspace || !originalImage) return;

    const pipeline = extractExecutablePipeline(workspace);
    if (pipeline.length === 0) {
      setError('No pipeline found. Add a "Read Image" block and connect operations.');
      return;
    }

    setExecuting(true);
    setError(null);
    setTiming(null);
    setActiveStepImage(null);
    setActiveStepAnalysis(null);
    setActiveStepHistogram(null);

    try {
      const response = await executePipeline({
        image: originalImage,
        image_format: imageFormat,
        pipeline,
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
      setError(err instanceof Error ? err.message : "Network error");
      setTiming(null);
    } finally {
      setExecuting(false);
    }
  };

  if (stepResults.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-xs text-gray-400 dark:text-gray-500 bg-white dark:bg-gray-800">
        Run the pipeline to see step results
      </div>
    );
  }

  const renderStepCard = (step: StepResult, isMacroChild: boolean = false) => {
    const key = getCardKey(step);
    const isActive =
      (activeStepBlockId && step.block_id === activeStepBlockId) ||
      (!activeStepBlockId && activeStepIndex === step.index);
    const label = getStepLabel(step.type);
    const isFinalStep = step === finalStep;

    return (
      <button
        key={key}
        ref={(node) => {
          cardRefs.current[key] = node;
        }}
        onClick={() => handleCardClick(step)}
        onDoubleClick={() => handleCardDoubleClick(step)}
        className={`w-32 h-40 flex-shrink-0 flex flex-col overflow-hidden rounded-md border bg-gray-50 dark:bg-gray-900 text-left transition-colors ${
          isActive
            ? "border-indigo-500 ring-2 ring-indigo-200 dark:ring-indigo-900"
            : step.success
              ? "border-gray-200 dark:border-gray-700 hover:border-indigo-300 dark:hover:border-indigo-600"
              : "border-red-300 dark:border-red-800"
        } ${workspaceDirty ? "opacity-55" : ""}`}
        title={`${step.type}. Double-click to enlarge.`}
      >
        <div className="h-24 flex items-center justify-center bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-700">
          {step.thumbnail ? (
            <img
              src={`data:image/${step.image_format ?? imageFormat};base64,${step.thumbnail}`}
              alt={`Step ${step.index}`}
              className="max-h-full max-w-full object-contain"
            />
          ) : (
            <ImageDown size={20} className="text-gray-300 dark:text-gray-600" />
          )}
        </div>
        <div className="min-h-0 flex-1 px-2 py-1.5">
          <div className="flex items-center gap-1">
            <span className="text-[11px] font-semibold text-gray-700 dark:text-gray-200">
              Step {step.index}
            </span>
            {isMacroChild && (
              <span className="rounded bg-indigo-50 dark:bg-indigo-900/40 px-1 py-0.2 text-[8px] font-medium uppercase text-indigo-600 dark:text-indigo-300">
                Macro
              </span>
            )}
            {isFinalStep && (
              <span className="rounded bg-emerald-50 dark:bg-emerald-900/30 px-1 py-0.5 text-[9px] font-semibold uppercase text-emerald-600 dark:text-emerald-400">
                Final
              </span>
            )}
            {isActive && isInspectingStep && (
              <Loader2 size={11} className="animate-spin text-indigo-500" />
            )}
          </div>
          <div className="truncate text-[10px] text-gray-500 dark:text-gray-400">{label}</div>
          {step.timing_ms !== null && step.timing_ms !== undefined && (
            <div className="text-[10px] text-gray-400 dark:text-gray-500">
              {step.timing_ms.toFixed(1)} ms
            </div>
          )}
          {!step.success && (
            <div className="truncate text-[10px] text-red-500 dark:text-red-400">
              {step.error ?? "Failed"}
            </div>
          )}
        </div>
      </button>
    );
  };

  const renderInlineMacro = (macroBlockId: string, steps: StepResult[]) => {
    const isCollapsed = collapsedMacros.has(macroBlockId);
    const macroName = getMacroDisplayName(macroBlockId);

    return (
      <div
        key={macroBlockId}
        className={`flex items-center gap-2 flex-shrink-0 p-1 rounded-lg border transition-all ${
          !isCollapsed
            ? "border-indigo-200 bg-indigo-50/30 dark:border-indigo-800/50 dark:bg-indigo-950/20"
            : "border-transparent"
        }`}
      >
        {/* Card-sized Inline Toggle Button with Chevron Arrow */}
        <button
          type="button"
          onClick={() => toggleMacroCollapse(macroBlockId)}
          className="h-40 px-3 flex flex-col items-center justify-center gap-2 border border-indigo-200 dark:border-indigo-700/60 bg-indigo-50/50 dark:bg-indigo-900/20 hover:bg-indigo-100/70 dark:hover:bg-indigo-900/40 rounded-md transition-colors text-indigo-700 dark:text-indigo-300"
          title={`${macroName} (${steps.length} steps). Click to toggle expansion.`}
        >
          <div className="flex items-center gap-1 font-semibold text-xs">
            {isCollapsed ? <ChevronRight size={18} /> : <ChevronDown size={18} />}
            <span className="truncate max-w-[90px]">{macroName}</span>
          </div>
          <span className="rounded bg-indigo-100 dark:bg-indigo-800/60 px-2 py-0.5 text-[10px] text-indigo-800 dark:text-indigo-200 font-medium">
            {steps.length} {steps.length === 1 ? "step" : "steps"}
          </span>
        </button>

        {/* Expands inner steps horizontally to the right */}
        {!isCollapsed && (
          <div className="flex items-center gap-2.5 pl-1 pr-1">
            {steps.map((step) => renderStepCard(step, true))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full bg-white dark:bg-gray-800 overflow-auto">
      {workspaceDirty && (
        <div className="sticky top-0 z-10 flex items-center gap-2 border-b border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/30 px-3 py-1.5 text-xs text-amber-700 dark:text-amber-300">
          <span className="font-semibold">Out of date</span>
          <span className="text-amber-600 dark:text-amber-400">
            Workspace changed after this run.
          </span>
          <button
            type="button"
            onClick={() => void handleRefresh()}
            disabled={isExecuting || !workspace || !originalImage}
            className="ml-auto inline-flex items-center gap-1 rounded border border-amber-300 dark:border-amber-700 px-2 py-0.5 font-medium hover:bg-amber-100 dark:hover:bg-amber-900/50 disabled:cursor-not-allowed disabled:opacity-50"
            title="Refresh step results"
          >
            {isExecuting ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
            Refresh
          </button>
        </div>
      )}

      {/* HORIZONTAL FILMSTRIP */}
      <div className="flex items-center gap-3 px-3 py-3 min-w-max">
        {inlineItems.map((item) =>
          item.kind === "step"
            ? renderStepCard(item.step)
            : renderInlineMacro(item.macroBlockId, item.steps),
        )}
      </div>

      {modalImageSrc && (
        <ImageModal
          isOpen={modalImageSrc !== null}
          imageSrc={modalImageSrc}
          onClose={() => setModalImageSrc(null)}
        />
      )}
    </div>
  );
}
