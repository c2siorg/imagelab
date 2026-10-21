/**
 * ImageComparisonSlider Component
 *
 * Multi-mode visual comparison engine integrated directly into ImageLab.
 * Combines industry-standard CV inspection paradigms:
 * 1. Split Wipe: Draggable divider bar with dual-image clipping, supporting both
 *    horizontal (left/right) and vertical (top/bottom) wipes.
 * 2. 2-Up Side-by-Side: Simultaneous dual-viewport comparison without occlusion.
 * 3. Difference Heatmap: Real-time Euclidean difference canvas with colormaps,
 *    gain amplification (1x-16x for subtle filter detection), and live MAE metrics.
 * 4. Hold & Auto-Blink: Instant toggle/hold (keyboard shortcut: \) and optical
 *    auto-blink inspection (1.5 Hz) for detecting micro-changes.
 */

import { useEffect, useRef, useState } from "react";
import {
  Columns,
  Eye,
  Flame,
  GripHorizontal,
  GripVertical,
  Maximize2,
  Pause,
  Play,
  RotateCcw,
  SplitSquareHorizontal,
  X,
} from "lucide-react";
import { useImageComparison } from "../../hooks/useImageComparison";
import {
  renderDiffToCanvas,
  type ColormapType,
  type PixelDiffMetrics,
} from "../../utils/imageDiff";

export type ComparisonMode = "split" | "side_by_side" | "heatmap" | "hold";
export type SplitOrientation = "vertical" | "horizontal";

export interface ImageComparisonSliderProps {
  originalSrc: string;
  processedSrc: string;
  originalLabel?: string;
  processedLabel?: string;
  onExpand?: () => void;
  onClose?: () => void;
}

export default function ImageComparisonSlider({
  originalSrc,
  processedSrc,
  originalLabel = "Original",
  processedLabel = "Processed",
  onExpand,
  onClose,
}: ImageComparisonSliderProps) {
  const [mode, setMode] = useState<ComparisonMode>("split");
  const [splitOrientation, setSplitOrientation] = useState<SplitOrientation>("vertical");
  const [colormap, setColormap] = useState<ColormapType>("thermal");
  const [diffGain, setDiffGain] = useState<number>(1);
  const [diffMetrics, setDiffMetrics] = useState<PixelDiffMetrics | null>(null);
  const [isHoldingBefore, setIsHoldingBefore] = useState<boolean>(false);
  const [isBlinking, setIsBlinking] = useState<boolean>(false);

  const heatmapCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const imgOriginalRef = useRef<HTMLImageElement | null>(null);
  const imgProcessedRef = useRef<HTMLImageElement | null>(null);

  const {
    position: splitPosition,
    containerRef,
    startDragging: startDrag,
    setPosition,
    setOrientation: setHookOrientation,
  } = useImageComparison({
    initialPosition: 50,
    initialOrientation: splitOrientation === "vertical" ? "horizontal" : "vertical",
  });

  useEffect(() => {
    setHookOrientation(splitOrientation === "vertical" ? "horizontal" : "vertical");
  }, [splitOrientation, setHookOrientation]);

  const stepPosition = (delta: number) => setPosition(splitPosition + delta);

  // Render Difference Heatmap onto canvas when mode is 'heatmap'
  useEffect(() => {
    if (mode !== "heatmap") return;
    const canvas = heatmapCanvasRef.current;
    const imgA = imgOriginalRef.current;
    const imgB = imgProcessedRef.current;

    if (!canvas || !imgA || !imgB) return;

    const computeHeatmap = () => {
      if (!imgA.naturalWidth || !imgB.naturalWidth) return;
      try {
        const metrics = renderDiffToCanvas(imgA, imgB, canvas, {
          colormap,
          gain: diffGain,
        });
        setDiffMetrics(metrics);
      } catch {
        setDiffMetrics(null);
      }
    };

    if (imgA.complete && imgB.complete) {
      computeHeatmap();
    }
    imgA.addEventListener("load", computeHeatmap);
    imgB.addEventListener("load", computeHeatmap);

    return () => {
      imgA.removeEventListener("load", computeHeatmap);
      imgB.removeEventListener("load", computeHeatmap);
    };
  }, [mode, colormap, diffGain, originalSrc, processedSrc]);

  // Global keyboard shortcut: Hold '\' to view original (Lightroom style)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "\\" && !e.repeat) {
        setIsHoldingBefore(true);
      }
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === "\\") {
        setIsHoldingBefore(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, []);

  // Auto-blink timer (1.5 Hz interval)
  useEffect(() => {
    if (!isBlinking || mode !== "hold") return;
    const interval = setInterval(() => {
      setIsHoldingBefore((prev) => !prev);
    }, 600);

    return () => {
      clearInterval(interval);
      setIsHoldingBefore(false);
    };
  }, [isBlinking, mode]);

  return (
    <div
      className="relative w-full h-full flex flex-col select-none overflow-hidden bg-gray-50 dark:bg-gray-900"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
          e.preventDefault();
          stepPosition(-5);
        } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
          e.preventDefault();
          stepPosition(5);
        }
      }}
    >
      {/* Hidden baseline image elements for canvas diff rendering */}
      <img
        ref={imgOriginalRef}
        src={originalSrc}
        alt="Baseline Hidden"
        className="hidden"
        crossOrigin="anonymous"
      />
      <img
        ref={imgProcessedRef}
        src={processedSrc}
        alt="Processed Hidden"
        className="hidden"
        crossOrigin="anonymous"
      />

      {/* Docked Sub-Toolbar Header */}
      <div className="h-8 px-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between flex-shrink-0 text-xs">
        {/* Mode Selector Tabs */}
        <div className="flex items-center gap-0.5 bg-gray-100 dark:bg-gray-700 p-0.5 rounded border border-gray-200 dark:border-gray-600">
          <button
            type="button"
            onClick={() => {
              setMode("split");
              setIsBlinking(false);
            }}
            className={`flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium transition-colors cursor-pointer ${
              mode === "split"
                ? "bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-xs"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
            }`}
            title="Split wipe curtain slider"
          >
            <SplitSquareHorizontal size={11} />
            Split
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("side_by_side");
              setIsBlinking(false);
            }}
            className={`flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium transition-colors cursor-pointer ${
              mode === "side_by_side"
                ? "bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-xs"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
            }`}
            title="Side-by-side 2-up dual view"
          >
            <Columns size={11} />
            2-Up
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("heatmap");
              setIsBlinking(false);
            }}
            className={`flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium transition-colors cursor-pointer ${
              mode === "heatmap"
                ? "bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-xs"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
            }`}
            title="Difference heatmap"
          >
            <Flame size={11} />
            Diff
          </button>
          <button
            type="button"
            onClick={() => setMode("hold")}
            className={`flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium transition-colors cursor-pointer ${
              mode === "hold"
                ? "bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-xs"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
            }`}
            title="Hold to view before (Shortcut: \)"
          >
            <Eye size={11} />
            Hold
          </button>
        </div>

        {/* Mode-Specific Secondary Controls */}
        <div className="flex items-center gap-1">
          {mode === "split" && (
            <button
              type="button"
              onClick={() =>
                setSplitOrientation((prev) => (prev === "vertical" ? "horizontal" : "vertical"))
              }
              className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600 transition-colors cursor-pointer"
              title="Toggle split wipe orientation (vertical / horizontal)"
            >
              <RotateCcw size={10} />
              {splitOrientation === "vertical" ? "Vert" : "Horiz"}
            </button>
          )}

          {mode === "heatmap" && (
            <div className="flex items-center gap-1">
              <select
                value={colormap}
                onChange={(e) => setColormap(e.target.value as ColormapType)}
                className="px-1 py-0.5 text-[10px] rounded bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 cursor-pointer"
              >
                <option value="thermal">Thermal</option>
                <option value="jet">Jet</option>
                <option value="grayscale">Grayscale</option>
              </select>

              {/* Gain Multiplier Buttons for Subtle Delta Detection */}
              <div
                className="flex items-center bg-gray-100 dark:bg-gray-700 rounded border border-gray-200 dark:border-gray-600 p-0.5"
                title="Sensitivity gain amplifier"
              >
                {[1, 2, 4, 8].map((g) => (
                  <button
                    key={g}
                    type="button"
                    onClick={() => setDiffGain(g)}
                    className={`px-1 py-0.5 text-[9px] font-medium rounded transition-colors cursor-pointer ${
                      diffGain === g
                        ? "bg-indigo-600 text-white"
                        : "text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
                    }`}
                  >
                    {g}x
                  </button>
                ))}
              </div>
            </div>
          )}

          {mode === "hold" && (
            <button
              type="button"
              onClick={() => setIsBlinking((prev) => !prev)}
              className={`flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border transition-colors cursor-pointer ${
                isBlinking
                  ? "bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border-amber-300 dark:border-amber-700"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:bg-gray-200"
              }`}
              title="Toggle automatic 1.5 Hz blink comparison"
            >
              {isBlinking ? <Pause size={10} /> : <Play size={10} />}
              Blink
            </button>
          )}

          {/* Action icons right */}
          {onExpand && (
            <button
              type="button"
              onClick={onExpand}
              className="p-1 rounded text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
              title="Expand full screen"
            >
              <Maximize2 size={12} />
            </button>
          )}

          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
              title="Close comparison"
            >
              <X size={12} />
            </button>
          )}
        </div>
      </div>

      {/* Main Viewport Stage */}
      <div className="flex-1 relative flex items-center justify-center overflow-hidden p-2">
        {mode === "split" && (
          <div
            ref={containerRef}
            className="relative max-w-full max-h-full flex items-center justify-center overflow-hidden"
            onPointerDown={(e) => startDrag(e.clientX, e.clientY)}
          >
            {/* Base layer: Processed Image */}
            <img
              src={processedSrc}
              alt={processedLabel}
              className="max-w-full max-h-full object-contain pointer-events-none select-none"
              draggable={false}
            />

            {/* Clipped overlay layer: Original Image */}
            <div
              className="absolute inset-0 overflow-hidden pointer-events-none"
              style={{
                clipPath:
                  splitOrientation === "vertical"
                    ? `polygon(0% 0%, ${splitPosition}% 0%, ${splitPosition}% 100%, 0% 100%)`
                    : `polygon(0% 0%, 100% 0%, 100% ${splitPosition}%, 0% ${splitPosition}%)`,
              }}
            >
              <img
                src={originalSrc}
                alt={originalLabel}
                className="w-full h-full object-contain pointer-events-none select-none"
                draggable={false}
              />
            </div>

            {/* Draggable divider seam */}
            {splitOrientation === "vertical" ? (
              <div
                className="absolute top-0 bottom-0 z-20 pointer-events-auto cursor-ew-resize flex items-center justify-center -translate-x-1/2"
                style={{ left: `${splitPosition}%` }}
                onPointerDown={(e) => startDrag(e.clientX, e.clientY)}
              >
                <div className="w-0.5 h-full bg-white shadow-md ring-1 ring-black/20" />
                <div className="absolute w-5 h-5 rounded-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 shadow-md flex items-center justify-center text-gray-600 dark:text-gray-300 hover:scale-110 transition-transform">
                  <GripVertical size={11} />
                </div>
              </div>
            ) : (
              <div
                className="absolute left-0 right-0 z-20 pointer-events-auto cursor-ns-resize flex items-center justify-center -translate-y-1/2"
                style={{ top: `${splitPosition}%` }}
                onPointerDown={(e) => startDrag(e.clientX, e.clientY)}
              >
                <div className="h-0.5 w-full bg-white shadow-md ring-1 ring-black/20" />
                <div className="absolute w-5 h-5 rounded-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 shadow-md flex items-center justify-center text-gray-600 dark:text-gray-300 hover:scale-110 transition-transform">
                  <GripHorizontal size={11} />
                </div>
              </div>
            )}

            {/* Badges indicating source */}
            <span className="absolute top-2 left-2 z-10 px-1.5 py-0.5 rounded bg-black/60 text-[9px] font-medium text-white backdrop-blur-xs">
              {originalLabel}
            </span>
            <span className="absolute top-2 right-2 z-10 px-1.5 py-0.5 rounded bg-black/60 text-[9px] font-medium text-white backdrop-blur-xs">
              {processedLabel}
            </span>
          </div>
        )}

        {mode === "side_by_side" && (
          <div className="w-full h-full flex flex-col sm:flex-row items-center justify-center gap-2 p-1 overflow-auto">
            <div className="flex-1 w-full h-full flex flex-col items-center justify-center relative bg-white/50 dark:bg-gray-800/50 rounded border border-gray-200 dark:border-gray-700 overflow-hidden p-1">
              <span className="absolute top-2 left-2 z-10 px-1.5 py-0.5 rounded bg-black/60 text-[9px] font-medium text-white backdrop-blur-xs">
                {originalLabel}
              </span>
              <img
                src={originalSrc}
                alt={originalLabel}
                className="max-w-full max-h-full object-contain"
                draggable={false}
              />
            </div>
            <div className="flex-1 w-full h-full flex flex-col items-center justify-center relative bg-white/50 dark:bg-gray-800/50 rounded border border-gray-200 dark:border-gray-700 overflow-hidden p-1">
              <span className="absolute top-2 left-2 z-10 px-1.5 py-0.5 rounded bg-black/60 text-[9px] font-medium text-white backdrop-blur-xs">
                {processedLabel}
              </span>
              <img
                src={processedSrc}
                alt={processedLabel}
                className="max-w-full max-h-full object-contain"
                draggable={false}
              />
            </div>
          </div>
        )}

        {mode === "heatmap" && (
          <div className="relative max-w-full max-h-full flex flex-col items-center justify-center">
            <canvas
              ref={heatmapCanvasRef}
              className="max-w-full max-h-full object-contain rounded shadow-xs"
            />
            {diffMetrics && (
              <div className="absolute bottom-1.5 left-2 right-2 z-30 pointer-events-none flex items-center justify-center">
                <div className="px-2 py-0.5 rounded-full bg-black/75 border border-white/20 text-white backdrop-blur-xs font-mono text-[9px] flex items-center gap-1.5 shadow-md">
                  <span>MAE: {diffMetrics.meanAbsoluteError}</span>
                  <span className="text-gray-500">•</span>
                  <span>Altered: {diffMetrics.alteredPercentage}%</span>
                  <span className="text-gray-500">•</span>
                  <span>Peak: {diffMetrics.peakDelta}</span>
                  {diffGain > 1 && (
                    <>
                      <span className="text-gray-500">•</span>
                      <span className="text-amber-300 font-semibold">Gain: {diffGain}x</span>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {mode === "hold" && (
          <div className="relative max-w-full max-h-full flex flex-col items-center justify-center">
            <img
              src={isHoldingBefore ? originalSrc : processedSrc}
              alt={isHoldingBefore ? originalLabel : processedLabel}
              className="max-w-full max-h-full object-contain pointer-events-none select-none"
              draggable={false}
            />

            {/* Active state badge */}
            <div className="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-black/70 text-[10px] font-medium text-white backdrop-blur-xs">
              {isHoldingBefore ? `Showing: ${originalLabel}` : `Showing: ${processedLabel}`}
            </div>

            {/* Hold Button at bottom */}
            <div className="absolute bottom-2 left-4 right-4 z-30">
              <button
                type="button"
                onPointerDown={() => setIsHoldingBefore(true)}
                onPointerUp={() => setIsHoldingBefore(false)}
                onPointerLeave={() => setIsHoldingBefore(false)}
                onPointerCancel={() => setIsHoldingBefore(false)}
                onMouseDown={() => setIsHoldingBefore(true)}
                onMouseUp={() => setIsHoldingBefore(false)}
                onTouchStart={() => setIsHoldingBefore(true)}
                onTouchEnd={() => setIsHoldingBefore(false)}
                className="w-full py-1.5 px-3 rounded bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white font-medium text-xs shadow-xs cursor-pointer select-none transition-colors text-center"
              >
                Press & Hold to View Original (or hold \ key)
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
