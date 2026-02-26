import { useState } from "react";
import { ZoomIn, ZoomOut, Image, ImageDown, Trash2 } from "lucide-react";
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

export default function PreviewPane() {
  const { originalImage, imageFormat, processedImage, error, errorStep, clearImage, totalDurationMs, stepTimings } =
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
        <div className="px-3 py-1.5 border-b border-gray-200 flex items-center gap-1.5">
          <ImageDown size={14} className="text-gray-400" />
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Processed
          </h2>
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
        {totalDurationMs !== null && (
          <div className="px-3 py-2 bg-white border-t border-gray-200">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-gray-600">Total Execution Time</span>
              <span className="text-gray-900 font-medium">{totalDurationMs.toFixed(1)} ms</span>
            </div>
            {stepTimings && stepTimings.length > 0 && (
              <details className="mt-1.5 group">
                <summary className="text-[10px] uppercase font-semibold text-gray-500 hover:text-indigo-600 cursor-pointer select-none">
                  Step breakdown
                </summary>
                <div className="mt-1 space-y-1">
                  {stepTimings.map((t, idx) => (
                    <div key={idx} className="flex justify-between text-[11px] text-gray-500">
                      <span className="truncate pr-2" title={t.type}>
                        <span className="text-gray-400 mr-1">{t.step}.</span>
                        {t.type}
                      </span>
                      <span className="flex-shrink-0 text-gray-600">{t.duration_ms.toFixed(1)} ms</span>
                    </div>
                  ))}
                </div>
              </details>
            )}
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
