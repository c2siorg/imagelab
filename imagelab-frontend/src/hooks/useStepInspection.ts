import { useCallback } from "react";
import { inspectPipelineStep } from "../api/pipeline";
import { usePipelineStore } from "../store/pipelineStore";
import type { StepInspectResponse, StepResult } from "../types/pipeline";

interface InspectStepOptions {
  clearAnalysis?: boolean;
}

let latestInspectionRequest = 0;

export function useStepInspection() {
  return useCallback(
    async (
      step: StepResult,
      options: InspectStepOptions = {},
    ): Promise<StepInspectResponse | null> => {
      const {
        executionId,
        setActiveStep,
        setActiveStepAnalysis,
        setActiveStepHistogram,
        setActiveStepImage,
        setInspectingStep,
        setPreviewImage,
        setError,
      } = usePipelineStore.getState();

      const requestId = latestInspectionRequest + 1;
      latestInspectionRequest = requestId;
      setActiveStep(step.block_id ?? null, step.index);
      if (options.clearAnalysis ?? true) {
        setActiveStepAnalysis(null);
        setActiveStepHistogram(null);
        setActiveStepImage(null);
      }

      if (!executionId || !step.block_id || !step.has_full_image) {
        setInspectingStep(false);
        return null;
      }

      setInspectingStep(true);
      try {
        const inspected = await inspectPipelineStep(executionId, step.block_id);
        const currentState = usePipelineStore.getState();
        const isLatestRequest = requestId === latestInspectionRequest;
        const isStillActiveStep =
          currentState.activeStepBlockId === step.block_id &&
          currentState.activeStepIndex === step.index;

        if (!isLatestRequest || !isStillActiveStep) return null;

        setPreviewImage(inspected.image);
        setActiveStepImage(inspected.image, inspected.image_format);
        setActiveStepAnalysis(inspected.analysis);
        setActiveStepHistogram(inspected.histogram);
        return inspected;
      } catch (err) {
        if (requestId !== latestInspectionRequest) return null;
        setError(err instanceof Error ? err.message : "Could not load step preview", step.index);
        return null;
      } finally {
        if (requestId === latestInspectionRequest) {
          setInspectingStep(false);
        }
      }
    },
    [],
  );
}
