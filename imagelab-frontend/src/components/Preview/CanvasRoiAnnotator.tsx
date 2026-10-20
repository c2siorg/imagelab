/**
 * CanvasRoiAnnotator Component
 *
 * Streamlined, non-intrusive on-canvas visual bounding box selection and ROI annotation tool.
 * Features docked top sub-toolbar (presets, apply, copy, clear) keeping the image 100% unobstructed,
 * 8-handle directional resizing, and a compact single-line measurement HUD (dimensions, Mean, StdDev).
 * Directly binds coordinates into Blockly spatial blocks (Crop Image / Draw Rectangle).
 */

import { useEffect, useMemo, useRef, useState } from "react";
import type * as Blockly from "blockly";
import { Check, Copy, RefreshCw, X } from "lucide-react";
import { useCanvasRoi } from "../../hooks/useCanvasRoi";
import {
  calculateRoiStatistics,
  imageToViewportCoordinates,
  type BoundingBox,
  type Dimensions,
  type ResizeHandle,
} from "../../utils/roiCoordinates";
import {
  calculateRoiMeasurements,
  extractImageDataFromImageElement,
} from "../../utils/pixelInspector";

export interface CanvasRoiAnnotatorProps {
  imageSrc: string;
  naturalWidth?: number;
  naturalHeight?: number;
  workspace?: Blockly.WorkspaceSvg | null;
  initialBox?: BoundingBox | null;
  onBoxChange?: (box: BoundingBox | null) => void;
  onClose?: () => void;
}

const ASPECT_RATIO_PRESETS = [
  { label: "Free", value: null },
  { label: "1:1", value: 1.0 },
  { label: "4:3", value: 4 / 3 },
  { label: "16:9", value: 16 / 9 },
];

const HANDLES: Array<{ type: ResizeHandle; cursor: string }> = [
  { type: "nw", cursor: "nwse-resize" },
  { type: "n", cursor: "ns-resize" },
  { type: "ne", cursor: "nesw-resize" },
  { type: "e", cursor: "ew-resize" },
  { type: "se", cursor: "nwse-resize" },
  { type: "s", cursor: "ns-resize" },
  { type: "sw", cursor: "nesw-resize" },
  { type: "w", cursor: "ew-resize" },
];

export default function CanvasRoiAnnotator({
  imageSrc,
  naturalWidth = 640,
  naturalHeight = 480,
  workspace = null,
  initialBox = null,
  onBoxChange,
  onClose,
}: CanvasRoiAnnotatorProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);

  const [naturalDims, setNaturalDims] = useState<Dimensions>({
    width: naturalWidth,
    height: naturalHeight,
  });

  const [displayDims, setDisplayDims] = useState<Dimensions>({ width: 0, height: 0 });
  const [cachedImageData, setCachedImageData] = useState<ImageData | null>(null);
  const [feedbackStatus, setFeedbackStatus] = useState<string | null>(null);
  const [hasCopied, setHasCopied] = useState<boolean>(false);

  const {
    roiBox,
    aspectRatio,
    setAspectRatio,
    startCreation,
    startMoving,
    startResizing,
    nudgeRoi,
    clearRoi,
    applyRoiToBlock,
  } = useCanvasRoi({
    naturalDimensions: naturalDims,
    containerRef,
    imageRef,
    initialBox,
    onBoxChange,
  });

  // Track rendered image element dimensions
  useEffect(() => {
    const img = imageRef.current;
    if (!img) return;

    const updateDisplayDimensions = () => {
      setDisplayDims({
        width: img.clientWidth,
        height: img.clientHeight,
      });
    };

    updateDisplayDimensions();

    const observer =
      typeof ResizeObserver !== "undefined" ? new ResizeObserver(updateDisplayDimensions) : null;

    if (observer) {
      observer.observe(img);
    }
    window.addEventListener("resize", updateDisplayDimensions);

    return () => {
      if (observer) {
        observer.disconnect();
      }
      window.removeEventListener("resize", updateDisplayDimensions);
    };
  }, []);

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setNaturalDims({
      width: img.naturalWidth || naturalWidth,
      height: img.naturalHeight || naturalHeight,
    });
    setDisplayDims({
      width: img.clientWidth,
      height: img.clientHeight,
    });
    setCachedImageData(extractImageDataFromImageElement(img));
  };

  // Compute ImageJ-style quantitative metrics from cached ImageData state
  const measurements = useMemo(() => {
    if (!roiBox || !cachedImageData) return null;
    return calculateRoiMeasurements(cachedImageData, roiBox);
  }, [roiBox, cachedImageData]);

  // Auto-dismiss transient feedback status
  useEffect(() => {
    if (!feedbackStatus) return;
    const timer = window.setTimeout(() => setFeedbackStatus(null), 2500);
    return () => window.clearTimeout(timer);
  }, [feedbackStatus]);

  const handleApplyToBlock = () => {
    if (!roiBox) return;
    const result = applyRoiToBlock(workspace);
    if (result.success) {
      setFeedbackStatus("Applied!");
    } else {
      setFeedbackStatus(result.message);
    }
  };

  const handleCopyCoordinates = async () => {
    if (!roiBox) return;
    const normX = Math.round(Math.min(roiBox.x1, roiBox.x2));
    const normY = Math.round(Math.min(roiBox.y1, roiBox.y2));
    const normW = Math.round(Math.abs(roiBox.x2 - roiBox.x1));
    const normH = Math.round(Math.abs(roiBox.y2 - roiBox.y1));

    const text = JSON.stringify({ x: normX, y: normY, width: normW, height: normH }, null, 2);
    try {
      await navigator.clipboard.writeText(text);
      setHasCopied(true);
      window.setTimeout(() => setHasCopied(false), 2000);
      setFeedbackStatus("Copied!");
    } catch {
      setFeedbackStatus("Failed to copy");
    }
  };

  const viewportBox = useMemo(() => {
    if (!roiBox || displayDims.width <= 0 || displayDims.height <= 0) return null;
    const p1 = imageToViewportCoordinates(
      { x: Math.min(roiBox.x1, roiBox.x2), y: Math.min(roiBox.y1, roiBox.y2) },
      displayDims,
      naturalDims,
    );
    const p2 = imageToViewportCoordinates(
      { x: Math.max(roiBox.x1, roiBox.x2), y: Math.max(roiBox.y1, roiBox.y2) },
      displayDims,
      naturalDims,
    );
    return {
      topLeft: p1,
      bottomRight: p2,
      width: Math.max(0, p2.x - p1.x),
      height: Math.max(0, p2.y - p1.y),
    };
  }, [roiBox, displayDims, naturalDims]);

  const stats = roiBox ? calculateRoiStatistics(roiBox, naturalDims) : null;

  return (
    <div
      className="absolute inset-0 z-20 flex flex-col select-none overflow-hidden bg-gray-50 dark:bg-gray-900"
      onKeyDown={(e) => {
        if (!roiBox) return;
        const step = e.shiftKey ? 10 : 1;
        if (e.key === "ArrowLeft") {
          e.preventDefault();
          nudgeRoi(-step, 0);
        } else if (e.key === "ArrowRight") {
          e.preventDefault();
          nudgeRoi(step, 0);
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          nudgeRoi(0, -step);
        } else if (e.key === "ArrowDown") {
          e.preventDefault();
          nudgeRoi(0, step);
        } else if (e.key === "Escape") {
          e.preventDefault();
          clearRoi();
        }
      }}
      tabIndex={0}
      role="region"
      aria-label="Interactive ROI selection canvas"
    >
      {/* Docked Sub-Toolbar Header: Clean, Compact, Never Obstructs the Image */}
      <div className="h-7.5 px-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between flex-shrink-0 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold text-gray-700 dark:text-gray-300">ROI</span>
          {/* Aspect Ratio Presets */}
          <div className="flex items-center gap-0.5 bg-gray-100 dark:bg-gray-700 p-0.5 rounded border border-gray-200 dark:border-gray-600">
            {ASPECT_RATIO_PRESETS.map((preset) => {
              const isSelected = aspectRatio === preset.value;
              return (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => setAspectRatio(preset.value)}
                  className={`px-1.5 py-0.5 rounded text-[10px] font-medium transition-colors cursor-pointer ${
                    isSelected
                      ? "bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-xs"
                      : "text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                  }`}
                  title={`Lock aspect ratio to ${preset.label}`}
                >
                  {preset.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Action Controls Right */}
        <div className="flex items-center gap-1">
          {roiBox && (
            <>
              <button
                type="button"
                onClick={handleApplyToBlock}
                className="h-5.5 px-2 rounded bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-[10px] shadow-xs cursor-pointer flex items-center gap-1 transition-colors"
                title="Apply coordinates to selected or workspace Crop/Draw block"
              >
                <Check size={11} />
                {feedbackStatus === "Applied!" ? "Applied!" : "Apply to Block"}
              </button>
              <button
                type="button"
                onClick={handleCopyCoordinates}
                className="p-1 rounded text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                title="Copy coordinates JSON to clipboard"
              >
                {hasCopied ? <Check size={11} className="text-indigo-600" /> : <Copy size={11} />}
              </button>
              <button
                type="button"
                onClick={clearRoi}
                className="p-1 rounded text-gray-400 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                title="Clear selection (Esc)"
              >
                <RefreshCw size={11} />
              </button>
            </>
          )}
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
              title="Close ROI Tool"
            >
              <X size={12} />
            </button>
          )}
        </div>
      </div>

      {/* Main Interactive Stage — 100% Unobstructed Image View */}
      <div
        ref={containerRef}
        className="flex-1 relative flex items-center justify-center overflow-hidden p-2 cursor-crosshair"
        onPointerDown={(e) => {
          if (e.target === e.currentTarget || (e.target as HTMLElement).tagName === "IMG") {
            startCreation(e.clientX, e.clientY);
          }
        }}
      >
        <img
          ref={imageRef}
          src={imageSrc}
          alt="ROI Base"
          onLoad={handleImageLoad}
          className="max-w-full max-h-full object-contain pointer-events-none select-none"
          draggable={false}
        />

        {/* SVG Spotlight & Coordinate Overlay */}
        {viewportBox && displayDims.width > 0 && displayDims.height > 0 && (
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              width: `${displayDims.width}px`,
              height: `${displayDims.height}px`,
              left: "50%",
              top: "50%",
              transform: "translate(-50%, -50%)",
            }}
          >
            {/* Spotlight darkened mask outside bounding box */}
            <svg
              className="w-full h-full absolute inset-0 pointer-events-none"
              viewBox={`0 0 ${displayDims.width} ${displayDims.height}`}
            >
              <defs>
                <mask id="roi-spotlight-mask">
                  <rect width="100%" height="100%" fill="white" />
                  <rect
                    x={viewportBox.topLeft.x}
                    y={viewportBox.topLeft.y}
                    width={viewportBox.width}
                    height={viewportBox.height}
                    fill="black"
                  />
                </mask>
              </defs>
              <rect
                width="100%"
                height="100%"
                fill="rgba(0, 0, 0, 0.45)"
                mask="url(#roi-spotlight-mask)"
              />
            </svg>

            {/* Bounding Box Frame & Drag Surface */}
            <div
              className="absolute pointer-events-auto cursor-move border-2 border-dashed border-white shadow-xs"
              style={{
                left: `${viewportBox.topLeft.x}px`,
                top: `${viewportBox.topLeft.y}px`,
                width: `${viewportBox.width}px`,
                height: `${viewportBox.height}px`,
              }}
              onPointerDown={(e) => {
                e.stopPropagation();
                startMoving(e.clientX, e.clientY);
              }}
            >
              {/* 8 Resize Handles */}
              {HANDLES.map(({ type, cursor }) => {
                let left = "50%";
                let top = "50%";

                if (type.includes("w")) left = "0%";
                if (type.includes("e")) left = "100%";
                if (type.includes("n")) top = "0%";
                if (type.includes("s")) top = "100%";

                return (
                  <div
                    key={type}
                    data-testid={`roi-handle-${type}`}
                    onPointerDown={(e) => {
                      e.stopPropagation();
                      startResizing(type, e.clientX, e.clientY);
                    }}
                    className="absolute w-2.5 h-2.5 bg-indigo-600 border border-white rounded-xs transform -translate-x-1/2 -translate-y-1/2 shadow-xs hover:scale-125 transition-transform"
                    style={{ left, top, cursor }}
                  />
                );
              })}
            </div>
          </div>
        )}

        {/* Sleek, Single-Line Translucent Bottom HUD: Never Clips or Obstructs */}
        {stats && (
          <div className="absolute bottom-1.5 left-2 right-2 pointer-events-none flex items-center justify-center">
            <div className="px-2 py-0.5 rounded-full bg-black/75 border border-white/20 text-white backdrop-blur-xs font-mono text-[9px] flex items-center gap-1.5 shadow-md">
              <span className="font-semibold text-white">
                {stats.width} × {stats.height} px
              </span>
              <span className="text-gray-400">
                ({roiBox ? Math.round(Math.min(roiBox.x1, roiBox.x2)) : 0},{" "}
                {roiBox ? Math.round(Math.min(roiBox.y1, roiBox.y2)) : 0})
              </span>
              {measurements && (
                <>
                  <span className="text-gray-500">•</span>
                  <span className="text-indigo-300">μ: {measurements.meanIntensity}</span>
                  <span className="text-gray-500">•</span>
                  <span className="text-indigo-300">σ: {measurements.stdDev}</span>
                </>
              )}
            </div>
          </div>
        )}

        {/* Feedback Alert Pill when no block found */}
        {feedbackStatus && feedbackStatus !== "Applied!" && feedbackStatus !== "Copied!" && (
          <div className="absolute bottom-8 left-3 right-3 text-[10px] text-center py-1 px-2 rounded bg-amber-50 dark:bg-amber-950/80 border border-amber-300 dark:border-amber-800 text-amber-800 dark:text-amber-200 shadow-md">
            {feedbackStatus}
          </div>
        )}
      </div>
    </div>
  );
}
