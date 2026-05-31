import { useCallback } from "react";
import { inspectPipelineStep } from "../api/pipeline";
import { usePipelineStore } from "../store/pipelineStore";
import type { StepInspectResponse, StepResult } from "../types/pipeline";

interface InspectStepOptions {
  clearAnalysis?: boolean;
}

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
        setActiveStepImage,
        setInspectingStep,
        setPreviewImage,
        setError,
      } = usePipelineStore.getState();

      setActiveStep(step.block_id ?? null, step.index);
      if (options.clearAnalysis ?? true) {
        setActiveStepAnalysis(null);
        setActiveStepImage(null);
      }

      if (!executionId || !step.block_id || !step.has_full_image) return null;

      setInspectingStep(true);
      try {
        const inspected = await inspectPipelineStep(executionId, step.block_id);
        setPreviewImage(inspected.image);
        setActiveStepImage(inspected.image, inspected.image_format);
        setActiveStepAnalysis(inspected.analysis);
        return inspected;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load step preview", step.index);
        return null;
      } finally {
        setInspectingStep(false);
      }
    },
    [],
  );
}
