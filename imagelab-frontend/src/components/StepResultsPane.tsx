import { useEffect, useMemo, useRef, useState } from "react";
import * as Blockly from "blockly";
import { ChevronDown, ChevronRight, ImageDown, Loader2, RefreshCw } from "lucide-react";
import { executePipeline, PipelineApiError } from "../api/pipeline";
import { extractExecutableGraph } from "../hooks/usePipeline";
import { useStepInspection } from "../hooks/useStepInspection";
import { usePipelineStore } from "../store/pipelineStore";
import { useMacroStore } from "../store/useMacroStore";
import type { StepResult, MacroStackFrame } from "../types/pipeline";
import ImageModal from "./Preview/ImageModal";

interface StepResultsPaneProps {
  workspace: Blockly.WorkspaceSvg | null;
}

interface MacroNode {
  id: string;
  name: string;
  children: Map<string, MacroNode>;
  steps: StepResult[];
  firstIndex: number;
}

/**
 * Builds a recursive tree structure from step results based on their macro_stack.
 * Tracks the minimum step index to maintain chronological rendering order.
 */
function buildMacroTree(steps: StepResult[]): Map<string, MacroNode> {
  const root = new Map<string, MacroNode>();

  for (const step of steps) {
    if (!step.macro_stack || step.macro_stack.length === 0) {
      continue;
    }

    let currentLevel = root;
    for (let i = 0; i < step.macro_stack.length; i++) {
      const frame = step.macro_stack[i];
      const frameId = frame.id;

      if (!currentLevel.has(frameId)) {
        currentLevel.set(frameId, {
          id: frameId,
          name: frame.name,
          children: new Map(),
          steps: [],
          firstIndex: step.index,
        });
      }

      const node = currentLevel.get(frameId)!;
      node.firstIndex = Math.min(node.firstIndex, step.index);

      if (i === step.macro_stack.length - 1) {
        node.steps.push(step);
      } else {
        currentLevel = node.children;
      }
    }
  }

  return root;
}

interface MacroGroupCardProps {
  node: MacroNode;
  depth: number;
  isCollapsed: boolean;
  onToggleCollapse: (id: string) => void;
  renderStepCard: (step: StepResult, isMacroChild: boolean) => React.ReactNode;
  getMacroDisplayName: (macroBlockId: string, macroStack?: MacroStackFrame[]) => string;
}

function MacroGroupCard({
  node,
  depth,
  isCollapsed,
  onToggleCollapse,
  renderStepCard,
  getMacroDisplayName,
}: MacroGroupCardProps) {
  const getDepthStyles = (d: number) => {
    const baseStyles =
      "flex items-center gap-2 flex-shrink-0 p-1.5 rounded-lg border transition-all";

    if (d === 0) {
      return `${baseStyles} ${
        !isCollapsed
          ? "border-indigo-200 bg-indigo-50/40 dark:border-indigo-800/60 dark:bg-indigo-950/30"
          : "border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/30"
      }`;
    } else if (d === 1) {
      return `${baseStyles} ${
        !isCollapsed
          ? "border-purple-200 bg-purple-50/40 dark:border-purple-800/60 dark:bg-purple-950/30"
          : "border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/30"
      }`;
    } else if (d === 2) {
      return `${baseStyles} ${
        !isCollapsed
          ? "border-pink-200 bg-pink-50/40 dark:border-pink-800/60 dark:bg-pink-950/30"
          : "border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/30"
      }`;
    } else {
      return `${baseStyles} ${
        !isCollapsed
          ? "border-slate-200 bg-slate-50/40 dark:border-slate-800/60 dark:bg-slate-950/30"
          : "border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/30"
      }`;
    }
  };

  const getButtonStyles = (d: number) => {
    const baseStyles =
      "h-40 px-3 flex flex-col items-center justify-center gap-2 border rounded-md transition-colors flex-shrink-0";

    if (d === 0) {
      return `${baseStyles} border-indigo-200 dark:border-indigo-700/60 bg-indigo-50/80 dark:bg-indigo-900/30 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300`;
    } else if (d === 1) {
      return `${baseStyles} border-purple-200 dark:border-purple-700/60 bg-purple-50/80 dark:bg-purple-900/30 hover:bg-purple-100 dark:hover:bg-purple-900/50 text-purple-700 dark:text-purple-300`;
    } else if (d === 2) {
      return `${baseStyles} border-pink-200 dark:border-pink-700/60 bg-pink-50/80 dark:bg-pink-900/30 hover:bg-pink-100 dark:hover:bg-pink-900/50 text-pink-700 dark:text-pink-300`;
    } else {
      return `${baseStyles} border-slate-200 dark:border-slate-700/60 bg-slate-50/80 dark:bg-slate-900/30 hover:bg-slate-100 dark:hover:bg-slate-900/50 text-slate-700 dark:text-slate-300`;
    }
  };

  const macroName = getMacroDisplayName(node.id, [{ id: node.id, name: node.name }]);
  const hasChildren = node.children.size > 0;

  const countTotalSteps = (n: MacroNode): number => {
    let total = n.steps.length;
    for (const child of n.children.values()) {
      total += countTotalSteps(child);
    }
    return total;
  };
  const totalSteps = countTotalSteps(node);

  return (
    <div className={getDepthStyles(depth)}>
      <button
        type="button"
        onClick={() => onToggleCollapse(node.id)}
        className={getButtonStyles(depth)}
        title={`${macroName} (${totalSteps} steps). Click to toggle expansion.`}
      >
        <div className="flex items-center gap-1 font-semibold text-xs">
          {isCollapsed ? <ChevronRight size={18} /> : <ChevronDown size={18} />}
          <span className="truncate max-w-[90px]">{macroName}</span>
        </div>
        <span className="rounded bg-white/60 dark:bg-black/30 px-2 py-0.5 text-[10px] font-medium">
          {totalSteps} {totalSteps === 1 ? "step" : "steps"}
          {hasChildren &&
            ` + ${node.children.size} ${node.children.size === 1 ? "group" : "groups"}`}
        </span>
      </button>

      {!isCollapsed && (
        <div className="flex items-center gap-2.5 pl-1 pr-1">
          {Array.from(node.children.entries()).map(([childId, childNode]) => (
            <MacroGroupCard
              key={childId}
              node={childNode}
              depth={depth + 1}
              isCollapsed={false}
              onToggleCollapse={onToggleCollapse}
              renderStepCard={renderStepCard}
              getMacroDisplayName={getMacroDisplayName}
            />
          ))}

          {node.steps.map((step) => renderStepCard(step, true))}
        </div>
      )}
    </div>
  );
}

function getStepLabel(operatorType: string): string {
  const underscoreIndex = operatorType.indexOf("_");
  return underscoreIndex !== -1 ? operatorType.slice(underscoreIndex + 1) : operatorType;
}

function getCardKey(step: StepResult): string {
  return step.block_id ?? String(step.index);
}

type FilmstripItem =
  | { type: "step"; step: StepResult; index: number }
  | { type: "macro"; id: string; node: MacroNode; index: number };

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
  const prevSelectedBlockIdRef = useRef<string | null>(null);
  const [modalImageSrc, setModalImageSrc] = useState<string | null>(null);
  const [collapsedMacros, setCollapsedMacros] = useState<Set<string>>(new Set());
  const inspectStep = useStepInspection();

  const finalStep = useMemo(
    () => [...stepResults].reverse().find((step) => step.success),
    [stepResults],
  );

  /**
   * Sorts top-level steps and root macro cards sequentially by execution step index.
   */
  const { filmstripItems, activeMacroBlockIds } = useMemo(() => {
    const topLevelSteps: StepResult[] = [];
    const macroSteps: StepResult[] = [];

    for (const step of stepResults) {
      if (step.macro_stack && step.macro_stack.length > 0) {
        macroSteps.push(step);
      } else {
        topLevelSteps.push(step);
      }
    }

    const macroTree = buildMacroTree(macroSteps);
    const macroIds: string[] = [];

    function collectIds(nodes: Map<string, MacroNode>) {
      for (const [id, node] of nodes.entries()) {
        macroIds.push(id);
        collectIds(node.children);
      }
    }
    collectIds(macroTree);

    const items: FilmstripItem[] = [];

    for (const step of topLevelSteps) {
      items.push({ type: "step", step, index: step.index });
    }

    for (const [id, node] of macroTree.entries()) {
      items.push({ type: "macro", id, node, index: node.firstIndex });
    }

    items.sort((a, b) => a.index - b.index);

    return { filmstripItems: items, activeMacroBlockIds: macroIds };
  }, [stepResults]);

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

  useEffect(() => {
    setCollapsedMacros((prev) => {
      const next = new Set(prev);
      for (const id of activeMacroBlockIds) {
        if (!next.has(id)) {
          next.add(id);
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

  const getMacroDisplayName = (macroBlockId: string, macroStack?: MacroStackFrame[]): string => {
    if (macroStack && macroStack.length > 0) {
      const topLevelMacro = macroStack[0];
      if (topLevelMacro.name && topLevelMacro.name !== topLevelMacro.id) {
        if (topLevelMacro.name.startsWith("macro_")) {
          const matched = macros.find((m) => m.id === topLevelMacro.name.replace(/^macro_/, ""));
          if (matched) {
            return matched.name;
          }
        }
        return topLevelMacro.name;
      }
    }

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

  /**
   * Clears previous block highlights and triggers native workspace.centerOnBlock()
   * and Blockly selection.
   */
  const selectWorkspaceBlock = (step: StepResult) => {
    if (!workspace) return;

    // Clear previous selection & highlight
    const prevBlockId = prevSelectedBlockIdRef.current;
    if (prevBlockId) {
      const prevBlock = workspace.getBlockById(prevBlockId);
      if (
        prevBlock &&
        typeof (prevBlock as unknown as { unselect?: () => void }).unselect === "function"
      ) {
        (prevBlock as unknown as { unselect: () => void }).unselect();
      }
    }
    workspace.highlightBlock(null);

    let targetBlock: Blockly.BlockSvg | null = null;

    // Resolve target block using exact ID, macro_stack traversal, or colon splitting
    if (step.block_id) {
      targetBlock = workspace.getBlockById(step.block_id) as Blockly.BlockSvg | null;
    }

    if (!targetBlock && step.macro_stack && step.macro_stack.length > 0) {
      for (let i = step.macro_stack.length - 1; i >= 0; i--) {
        const frameId = step.macro_stack[i].id;
        targetBlock = workspace.getBlockById(frameId) as Blockly.BlockSvg | null;
        if (targetBlock) break;
      }
    }

    if (!targetBlock && step.block_id && step.block_id.includes(":")) {
      const candidateId = step.block_id.split(":")[0];
      targetBlock = workspace.getBlockById(candidateId) as Blockly.BlockSvg | null;
    }

    if (targetBlock) {
      // Center canvas on block and apply Blockly selection
      workspace.centerOnBlock(targetBlock.id);

      if (Blockly.common && typeof Blockly.common.setSelected === "function") {
        Blockly.common.setSelected(targetBlock);
      } else if (typeof (targetBlock as unknown as { select?: () => void }).select === "function") {
        (targetBlock as unknown as { select: () => void }).select();
      }

      workspace.highlightBlock(targetBlock.id);
      prevSelectedBlockIdRef.current = targetBlock.id;
    } else {
      prevSelectedBlockIdRef.current = null;
    }
  };

  const handleStepClick = async (step: StepResult) => {
    selectWorkspaceBlock(step);
    await inspectStep(step);
  };

  const handleStepDoubleClick = async (step: StepResult) => {
    selectWorkspaceBlock(step);
    const inspected = await inspectStep(step);
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

    const graph = extractExecutableGraph(workspace);
    if (graph.nodes.length === 0) {
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
              {step.error
                ? step.error
                    .replace(/arithm\.cpp:\d+.*$/, "")
                    .replace(/cv::Error:.*/, "")
                    .trim() || "Failed"
                : "Failed"}
            </div>
          )}
        </div>
      </button>
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

      {/* CHRONOLOGICAL FILMSTRIP (Ordered by Step Index) */}
      <div className="flex items-center gap-3 px-3 py-3 min-w-max">
        {filmstripItems.map((item) => {
          if (item.type === "step") {
            return renderStepCard(item.step, false);
          }
          return (
            <MacroGroupCard
              key={item.id}
              node={item.node}
              depth={0}
              isCollapsed={collapsedMacros.has(item.id)}
              onToggleCollapse={toggleMacroCollapse}
              renderStepCard={renderStepCard}
              getMacroDisplayName={getMacroDisplayName}
            />
          );
        })}
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
