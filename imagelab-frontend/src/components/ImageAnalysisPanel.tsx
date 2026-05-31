import { BarChart3, Loader2 } from "lucide-react";
import { usePipelineStore } from "../store/pipelineStore";
import HistogramCanvas from "./HistogramCanvas";
import StatsGrid from "./StatsGrid";

function EmptyState({ message }: { message: string }) {
  return (
    <div className="h-full flex items-center justify-center text-xs text-gray-400 dark:text-gray-500 bg-white dark:bg-gray-800">
      {message}
    </div>
  );
}

export default function ImageAnalysisPanel() {
  const {
    stepResults,
    activeStepBlockId,
    activeStepIndex,
    activeStepImage,
    activeStepImageFormat,
    activeStepAnalysis,
    isInspectingStep,
    workspaceDirty,
    imageFormat,
  } = usePipelineStore();

  if (stepResults.length === 0) {
    return <EmptyState message="Run the pipeline to inspect image analysis" />;
  }

  if (!activeStepBlockId && activeStepIndex === null) {
    return <EmptyState message="Select a step to view its histogram and stats" />;
  }

  if (isInspectingStep && !activeStepAnalysis) {
    return (
      <div className="h-full flex items-center justify-center gap-2 text-xs text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800">
        <Loader2 size={14} className="animate-spin" />
        Loading step analysis
      </div>
    );
  }

  if (!activeStepAnalysis || !activeStepImage) {
    return (
      <EmptyState message="Click a step result or matching workspace block to load analysis" />
    );
  }

  const selectedStepLabel =
    activeStepIndex !== null ? `Step ${activeStepIndex}` : (activeStepBlockId ?? "Selected step");

  return (
    <div className="h-full min-h-0 bg-white dark:bg-gray-800 overflow-auto">
      {workspaceDirty && (
        <div className="sticky top-0 z-10 border-b border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/30 px-3 py-1.5 text-xs text-amber-700 dark:text-amber-300">
          <span className="font-semibold">Out of date</span>
          <span className="ml-2 text-amber-600 dark:text-amber-400">
            Analysis belongs to the previous run.
          </span>
        </div>
      )}
      <div className="grid h-full min-h-[180px] grid-cols-1 lg:grid-cols-[minmax(220px,0.9fr)_minmax(300px,1.1fr)] gap-3 p-3">
        <section className="min-h-0 flex flex-col gap-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 dark:text-gray-300">
            <BarChart3 size={14} className="text-indigo-500" />
            <span>Histogram Section</span>
            <span className="ml-auto text-[10px] font-medium text-gray-400 dark:text-gray-500">
              {selectedStepLabel}
            </span>
          </div>
          <HistogramCanvas
            image={activeStepImage}
            format={activeStepImageFormat ?? imageFormat}
            channels={activeStepAnalysis.channels}
          />
        </section>
        <section className="min-h-0 flex flex-col gap-2">
          <div className="text-xs font-semibold text-gray-600 dark:text-gray-300">Stats</div>
          <StatsGrid analysis={activeStepAnalysis} />
        </section>
      </div>
    </div>
  );
}
