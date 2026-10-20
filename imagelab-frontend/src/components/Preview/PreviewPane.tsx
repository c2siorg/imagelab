import { useRef, useState } from "react";
import type * as Blockly from "blockly";
import {
  Camera,
  Crop,
  Crosshair,
  Image,
  ImageDown,
  SplitSquareHorizontal,
  Timer,
  Trash2,
  Upload,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { usePipelineStore } from "../../store/pipelineStore";
import { getImageFormatFromMimeType } from "../../utils/imageData";
import CanvasRoiAnnotator from "./CanvasRoiAnnotator";
import ImageComparisonModal from "./ImageComparisonModal";
import ImageComparisonSlider from "./ImageComparisonSlider";
import ImageDisplay from "./ImageDisplay";
import PixelInspectorOverlay from "./PixelInspectorOverlay";

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
    <div className="flex justify-center gap-1 p-1.5 border-t border-gray-200 dark:border-gray-700">
      <button
        onClick={onZoomIn}
        disabled={disabled}
        className="flex items-center justify-center p-1.5 border border-gray-300 dark:border-gray-600 rounded-md cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title="Zoom In"
      >
        <ZoomIn size={14} />
      </button>
      <button
        onClick={onZoomOut}
        disabled={disabled}
        className="flex items-center justify-center p-1.5 border border-gray-300 dark:border-gray-600 rounded-md cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title="Zoom Out"
      >
        <ZoomOut size={14} />
      </button>
    </div>
  );
}

function getStepLabel(operatorType: string): string {
  const underscoreIndex = operatorType.indexOf("_");
  return underscoreIndex !== -1 ? operatorType.slice(underscoreIndex + 1) : operatorType;
}

export interface PreviewPaneProps {
  workspace?: Blockly.WorkspaceSvg | null;
}

export default function PreviewPane({ workspace = null }: PreviewPaneProps) {
  const {
    originalImage,
    imageFormat,
    processedImage,
    activeStepImage,
    activeStepImageFormat,
    activeStepIndex,
    isInspectingStep,
    error,
    errorStep,
    clearImage,
    timings,
    isReadOnly,
    setOriginalImage,
    openCameraModal,
  } = usePipelineStore();

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isRoiActive, setIsRoiActive] = useState<boolean>(false);
  const [isCompareActive, setIsCompareActive] = useState<boolean>(false);
  const [isComparisonModalOpen, setIsComparisonModalOpen] = useState<boolean>(false);
  const [isInspectorActive, setIsInspectorActive] = useState<boolean>(false);

  const [originalZoom, setOriginalZoom] = useState<number | null>(null);
  const [processedZoom, setProcessedZoom] = useState<number | null>(null);

  const originalContainerRef = useRef<HTMLDivElement | null>(null);
  const originalImageRef = useRef<HTMLImageElement | null>(null);
  const processedContainerRef = useRef<HTMLDivElement | null>(null);
  const processedImageRef = useRef<HTMLImageElement | null>(null);

  const zoomIn = (setter: React.Dispatch<React.SetStateAction<number | null>>) => () =>
    setter((prev) => Math.min((prev ?? 300) + 100, 2500));
  const zoomOut = (setter: React.Dispatch<React.SetStateAction<number | null>>) => () =>
    setter((prev) => Math.max((prev ?? 300) - 100, 100));

  const handleFileUpload: React.ChangeEventHandler<HTMLInputElement> = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = typeof reader.result === "string" ? reader.result : "";
      const [, base64 = ""] = dataUrl.split(",", 2);
      if (!base64) return;

      const format = getImageFormatFromMimeType(file.type);
      setOriginalImage(base64, format, file.name);
    };
    reader.readAsDataURL(file);
    event.target.value = "";
  };

  const handleCameraOpen = () => {
    openCameraModal(({ image, format, label }) => {
      setOriginalImage(image, format, label);
    });
  };

  const originalSrc = originalImage ? `data:image/${imageFormat};base64,${originalImage}` : "";
  const targetImage = isInspectingStep && activeStepImage ? activeStepImage : processedImage;
  const targetFormat =
    (isInspectingStep && activeStepImage ? activeStepImageFormat : imageFormat) || imageFormat;
  const processedSrc = targetImage ? `data:image/${targetFormat};base64,${targetImage}` : "";
  const processedLabel =
    isInspectingStep && activeStepIndex !== null ? `Step ${activeStepIndex}` : "Processed";

  return (
    <div className="w-80 h-full bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col flex-shrink-0">
      {/* Original Image Card — Top Half */}
      <div className="flex-1 flex flex-col min-h-0 border-b border-gray-200 dark:border-gray-700">
        <div className="px-3 py-1.5 border-b border-gray-200 dark:border-gray-700 flex items-center gap-1.5">
          <Image size={14} className="text-gray-400" />
          <h2 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            Original
          </h2>
          <div className="ml-auto flex items-center gap-1">
            <button
              type="button"
              onClick={() => setIsRoiActive((prev) => !prev)}
              disabled={!originalImage}
              className={`p-1 rounded cursor-pointer transition-colors ${
                isRoiActive
                  ? "bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 ring-1 ring-indigo-500/30"
                  : "hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              } disabled:opacity-40 disabled:cursor-not-allowed`}
              title="Interactive Canvas ROI Selection"
              aria-label="Interactive Canvas ROI Selection"
            >
              <Crop size={14} />
            </button>
            {isReadOnly && (
              <>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleFileUpload}
                  aria-label="Upload image file"
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="p-1 rounded hover:bg-indigo-50 dark:hover:bg-indigo-900/30 text-gray-400 hover:text-indigo-500 transition-colors"
                  title="Upload image"
                  aria-label="Upload image"
                >
                  <Upload size={14} />
                </button>
                <button
                  type="button"
                  onClick={handleCameraOpen}
                  className="p-1 rounded hover:bg-indigo-50 dark:hover:bg-indigo-900/30 text-gray-400 hover:text-indigo-500 transition-colors"
                  title="Capture image"
                  aria-label="Capture image"
                >
                  <Camera size={14} />
                </button>
              </>
            )}
            {originalImage && (
              <button
                type="button"
                onClick={clearImage}
                className="p-1 rounded cursor-pointer hover:bg-red-50 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-500 transition-colors"
                title="Remove image"
                aria-label="Remove image"
              >
                <Trash2 size={14} />
              </button>
            )}
          </div>
        </div>

        <div
          ref={originalContainerRef}
          className="flex-1 relative flex items-center justify-center p-3 bg-gray-50 dark:bg-gray-900 overflow-hidden"
        >
          {originalImage ? (
            isRoiActive ? (
              <CanvasRoiAnnotator
                imageSrc={originalSrc}
                workspace={workspace}
                onClose={() => setIsRoiActive(false)}
              />
            ) : (
              <ImageDisplay
                imageRef={originalImageRef}
                image={originalImage}
                format={imageFormat}
                zoomWidth={originalZoom}
                alt="Original"
              >
                <PixelInspectorOverlay
                  imageRef={originalImageRef}
                  containerRef={originalContainerRef}
                  active={isInspectorActive}
                  imageSrc={originalSrc}
                />
              </ImageDisplay>
            )
          ) : (
            <p className="text-sm text-center text-gray-500 dark:text-gray-400">
              Drag a Read Image block from the Basic category of the Blocks panel, then click its
              upload or camera icon to load an image
            </p>
          )}
        </div>

        <ZoomControls
          disabled={!originalImage}
          onZoomIn={zoomIn(setOriginalZoom)}
          onZoomOut={zoomOut(setOriginalZoom)}
        />
      </div>

      {/* Processed Image Card — Bottom Half */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between px-3 py-1.5 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-1.5">
            <ImageDown size={14} className="text-gray-400" />
            <h2 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {processedLabel}
            </h2>
            {timings && !error && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 text-[11px] font-medium text-green-700 dark:text-green-400 ml-1 mt-[-1px]">
                <Timer size={10} className="text-green-600 dark:text-green-400" />
                {timings.total_ms.toFixed(1)} ms
              </span>
            )}
            {timings && error && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800 text-[11px] font-medium text-amber-700 dark:text-amber-400 ml-1 mt-[-1px]">
                <Timer size={10} className="text-amber-600 dark:text-amber-400" />
                {timings.total_ms.toFixed(1)} ms (partial)
              </span>
            )}
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setIsCompareActive((prev) => !prev)}
              disabled={!originalImage || !targetImage}
              className={`p-1 rounded cursor-pointer transition-colors ${
                isCompareActive
                  ? "bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 ring-1 ring-indigo-500/30"
                  : "hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              } disabled:opacity-40 disabled:cursor-not-allowed`}
              title="Inline Before/After Split Comparison & Difference Heatmap"
              aria-label="Inline Before/After Split Comparison & Difference Heatmap"
            >
              <SplitSquareHorizontal size={14} />
            </button>
            <button
              type="button"
              onClick={() => setIsInspectorActive((prev) => !prev)}
              disabled={!targetImage}
              className={`p-1 rounded cursor-pointer transition-colors ${
                isInspectorActive
                  ? "bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 ring-1 ring-indigo-500/30"
                  : "hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              } disabled:opacity-40 disabled:cursor-not-allowed`}
              title="Pixel Inspector & 5x5 Neighborhood Grid"
              aria-label="Pixel Inspector & 5x5 Neighborhood Grid"
            >
              <Crosshair size={14} />
            </button>
          </div>
        </div>

        <div
          ref={processedContainerRef}
          className="flex-1 relative flex items-center justify-center p-3 bg-gray-50 dark:bg-gray-900 overflow-hidden"
        >
          {targetImage ? (
            isCompareActive && originalSrc ? (
              <ImageComparisonSlider
                originalSrc={originalSrc}
                processedSrc={processedSrc}
                originalLabel="Original"
                processedLabel={processedLabel}
                onExpand={() => setIsComparisonModalOpen(true)}
                onClose={() => setIsCompareActive(false)}
              />
            ) : (
              <ImageDisplay
                imageRef={processedImageRef}
                image={targetImage}
                format={targetFormat}
                zoomWidth={processedZoom}
                alt={processedLabel}
              >
                <PixelInspectorOverlay
                  imageRef={processedImageRef}
                  containerRef={processedContainerRef}
                  active={isInspectorActive}
                  imageSrc={processedSrc}
                />
              </ImageDisplay>
            )
          ) : (
            <p className="text-sm text-center text-gray-500 dark:text-gray-400">
              {originalImage
                ? "Run the pipeline to see results"
                : "Load an image and run the pipeline to see results"}
            </p>
          )}
        </div>

        {error && (
          <div className="px-3 py-2 bg-red-50 dark:bg-red-900/30 border-t border-red-200 dark:border-red-800">
            <p className="text-xs text-red-600 dark:text-red-400 font-semibold mb-0.5">
              {errorStep !== null ? `Error in Step ${errorStep}` : "Pipeline Error"}
            </p>
            <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {timings && timings.steps.length > 0 && (
          <div className="px-3 py-2 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
            <details className="group">
              <summary className="text-[10px] uppercase font-semibold text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 cursor-pointer select-none">
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
                        className="flex items-center gap-2 text-[11px] text-gray-500 dark:text-gray-400"
                      >
                        <span className="w-4 text-right text-gray-400 dark:text-gray-500 flex-shrink-0">
                          {t.step}.
                        </span>
                        <span className="truncate flex-1 pr-1" title={t.operator_type}>
                          {label}
                        </span>
                        <div className="w-16 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full flex-shrink-0">
                          <div
                            className="h-full bg-indigo-400 rounded-full"
                            style={{ width: `${barWidth}%` }}
                          />
                        </div>
                        <span className="flex-shrink-0 text-gray-600 dark:text-gray-300 w-14 text-right">
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
          disabled={!targetImage}
          onZoomIn={zoomIn(setProcessedZoom)}
          onZoomOut={zoomOut(setProcessedZoom)}
        />
      </div>

      {isComparisonModalOpen && originalSrc && processedSrc && (
        <ImageComparisonModal
          isOpen={isComparisonModalOpen}
          onClose={() => setIsComparisonModalOpen(false)}
          originalSrc={originalSrc}
          processedSrc={processedSrc}
          originalLabel="Original"
          processedLabel={processedLabel}
        />
      )}
    </div>
  );
}
