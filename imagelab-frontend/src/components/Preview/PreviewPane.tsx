import { useState } from "react";
import { ZoomIn, ZoomOut, Image, ImageDown, Trash2, Timer } from "lucide-react";
import { usePipelineStore } from "../../store/pipelineStore";
import ImageDisplay from "./ImageDisplay";

function ZoomControls({
  disabled,
  onZoomIn,
  onZoomOut,
}: {
  disabled: boolean;
  onZoomIn: () => void;
  onZoomOut: () => void;
}) {
  return (
    <div className="flex justify-center gap-1 p-1.5 border-t border-gray-200">
      <button
        onClick={onZoomIn}
        disabled={disabled}
        className="flex items-center justify-center p-1.5 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title="Zoom In"
      >
        <ZoomIn size={14} />
      </button>
      <button
        onClick={onZoomOut}
        disabled={disabled}
        className="flex items-center justify-center p-1.5 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title="Zoom Out"
      >
        <ZoomOut size={14} />
      </button>
    </div>
  );
}

// Operator types follow 'category_operationName' convention; strip the category prefix for display.
function getStepLabel(operatorType: string): string {
  const underscoreIndex = operatorType.indexOf("_");
  return underscoreIndex !== -1 ? operatorType.slice(underscoreIndex + 1) : operatorType;
}

export default function PreviewPane() {
  const { originalImage, imageFormat, processedImage, error, errorStep, clearImage, timings } =
    usePipelineStore();
  const [originalZoom, setOriginalZoom] = useState<number | null>(null);
  const [processedZoom, setProcessedZoom] = useState<number | null>(null);

  const zoomIn = (setter: React.Dispatch<React.SetStateAction<number | null>>) => () =>
    setter((prev) => Math.min((prev ?? 300) + 100, 2500));
  const zoomOut = (setter: React.Dispatch<React.SetStateAction<number | null>>) => () =>
    setter((prev) => Math.max((prev ?? 300) - 100, 100));

  return (
    <div className="w-80 h-full bg-white border-l border-gray-200 flex flex-col flex-shrink-0">
      {/* Original image — top half */}
      <div className="flex-1 flex flex-col min-h-0 border-b border-gray-200">
        <div className="px-3 py-1.5 border-b border-gray-200 flex items-center gap-1.5">
          <Image size={14} className="text-gray-400" />
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Original</h2>
          {originalImage && (
            <button
              onClick={clearImage}
              className="ml-auto p-1 rounded hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
              title="Remove image"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
        <div className="flex-1 flex items-center justify-center p-3 bg-gray-50 overflow-auto">
          {originalImage ? (
            <ImageDisplay image={originalImage} format={imageFormat} zoomWidth={originalZoom} />
          ) : (
            <p className="text-sm text-gray-400">Use the Read Image block to upload</p>
          )}
        </div>
        <ZoomControls
          disabled={!originalImage}
          onZoomIn={zoomIn(setOriginalZoom)}
          onZoomOut={zoomOut(setOriginalZoom)}
        />
      </div>

      {/* Processed image — bottom half */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between px-3 py-1.5 border-b border-gray-200">
          <div className="flex items-center gap-1.5">
            <ImageDown size={14} className="text-gray-400" />
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Processed
            </h2>
            {timings && !error && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-50 border border-green-200 text-[11px] font-medium text-green-700 ml-1 mt-[-1px]">
                <Timer size={10} className="text-green-600" />
                {timings.total_ms.toFixed(1)} ms
              </span>
            )}
            {timings && error && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-[11px] font-medium text-amber-700 ml-1 mt-[-1px]">
                <Timer size={10} className="text-amber-600" />
                {timings.total_ms.toFixed(1)} ms (partial)
              </span>
            )}
          </div>
        </div>
        <div className="flex-1 flex items-center justify-center p-3 bg-gray-50 overflow-auto">
          {processedImage ? (
            <ImageDisplay image={processedImage} format={imageFormat} zoomWidth={processedZoom} />
          ) : (
            <p className="text-sm text-gray-400">
              {originalImage ? "Run the pipeline to see results" : "No image loaded"}
            </p>
          )}
        </div>
        {error && (
          <div className="px-3 py-2 bg-red-50 border-t border-red-200">
            <p className="text-xs text-red-600 font-semibold mb-0.5">
              {errorStep !== null ? `Error in Step ${errorStep}` : "Pipeline Error"}
            </p>
            <p className="text-xs text-red-600">{error}</p>
          </div>
        )}
        {timings && timings.steps.length > 0 && (
          <div className="px-3 py-2 bg-white border-t border-gray-200">
            <details className="group">
              <summary className="text-[10px] uppercase font-semibold text-gray-500 hover:text-indigo-600 cursor-pointer select-none">
                Step Timings
              </summary>
              <div className="mt-1.5 space-y-1">
                {(() => {
                  const maxMs = timings.steps.reduce((max, s) => Math.max(max, s.duration_ms), 0);
                  return timings.steps.map((t) => {
                    const label = getStepLabel(t.operator_type);
                    const barWidth = maxMs > 0 ? (t.duration_ms / maxMs) * 100 : 0;
                    return (
                      <div
                        key={t.step}
                        className="flex items-center gap-2 text-[11px] text-gray-500"
                      >
                        <span className="w-4 text-right text-gray-400 flex-shrink-0">
                          {t.step}.
                        </span>
                        <span className="truncate flex-1 pr-1" title={t.operator_type}>
                          {label}
                        </span>
                        <div className="w-16 h-1.5 bg-gray-100 rounded-full flex-shrink-0">
                          <div
                            className="h-full bg-indigo-400 rounded-full"
                            style={{ width: `${barWidth}%` }}
                          />
                        </div>
                        <span className="flex-shrink-0 text-gray-600 w-14 text-right">
                          {t.duration_ms.toFixed(1)} ms
                        </span>
                      </div>
                    );
                  });
                })()}
              </div>
            </details>
          </div>
        )}
        <ZoomControls
          disabled={!processedImage}
          onZoomIn={zoomIn(setProcessedZoom)}
          onZoomOut={zoomOut(setProcessedZoom)}
        />
      </div>
    </div>
  );
}
