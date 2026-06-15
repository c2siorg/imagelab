import { useEffect, useRef, useState } from "react";
import * as Blockly from "blockly";
import { ImageDown, Loader2, RefreshCw } from "lucide-react";
import { executePipeline } from "../api/pipeline";
import { extractPipeline } from "../hooks/usePipeline";
import { useStepInspection } from "../hooks/useStepInspection";
import { usePipelineStore } from "../store/pipelineStore";
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
  const cardRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const clickTimeoutRef = useRef<number | null>(null);
  const [modalImageSrc, setModalImageSrc] = useState<string | null>(null);
  const inspectStep = useStepInspection();

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
    // Delay single-click so double-click can open the modal without duplicate fetches.
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

    const pipeline = extractPipeline(workspace);
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

  const finalStep = [...stepResults].reverse().find((step) => step.success);

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
      <div className="flex items-start gap-3 px-3 py-3 min-w-max">
        {stepResults.map((step) => {
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
