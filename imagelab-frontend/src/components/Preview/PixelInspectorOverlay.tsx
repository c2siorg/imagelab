/**
 * PixelInspectorOverlay Component
 *
 * Real-time sub-pixel probe and 5x5 neighborhood loupe modeled after ImageJ's Pixel Inspection Tool.
 * Displays intrinsic raster coordinate (X, Y), RGB channel values, Hex color code, and ITU-R BT.601
 * perceptual luminance for immediate verification of filter effects and threshold boundaries.
 */

import { useEffect, useRef, useState } from "react";
import {
  extractImageDataFromImageElement,
  getPixelNeighborhood,
  probePixel,
  type PixelProbe,
} from "../../utils/pixelInspector";

export interface PixelInspectorOverlayProps {
  imageRef: React.RefObject<HTMLImageElement | null>;
  containerRef: React.RefObject<HTMLDivElement | null>;
  active: boolean;
  imageSrc?: string;
}

export default function PixelInspectorOverlay({
  imageRef,
  containerRef,
  active,
  imageSrc,
}: PixelInspectorOverlayProps) {
  const [probe, setProbe] = useState<PixelProbe | null>(null);
  const [matrix, setMatrix] = useState<(PixelProbe | null)[][] | null>(null);
  const [clientPos, setClientPos] = useState<{ x: number; y: number } | null>(null);
  const [showLoupe, setShowLoupe] = useState<boolean>(false);
  const cachedImageDataRef = useRef<ImageData | null>(null);

  useEffect(() => {
    if (!active) return;
    const container = containerRef.current;
    if (!container) return;

    cachedImageDataRef.current = imageRef.current
      ? extractImageDataFromImageElement(imageRef.current)
      : null;

    const handlePointerMove = (e: PointerEvent) => {
      const img = imageRef.current;
      if (!img || !img.naturalWidth || !img.naturalHeight) return;

      const rect = img.getBoundingClientRect();
      const clientX = e.clientX;
      const clientY = e.clientY;

      // Check if pointer is within rendered image bounds
      if (
        clientX < rect.left ||
        clientX > rect.right ||
        clientY < rect.top ||
        clientY > rect.bottom
      ) {
        setProbe(null);
        setMatrix(null);
        setClientPos(null);
        return;
      }

      const scaleX = img.naturalWidth / rect.width;
      const scaleY = img.naturalHeight / rect.height;

      const imgX = Math.floor((clientX - rect.left) * scaleX);
      const imgY = Math.floor((clientY - rect.top) * scaleY);

      if (!cachedImageDataRef.current) {
        cachedImageDataRef.current = extractImageDataFromImageElement(img);
      }

      if (cachedImageDataRef.current) {
        const probed = probePixel(cachedImageDataRef.current, imgX, imgY);
        setProbe(probed);

        if (showLoupe || e.shiftKey) {
          const hood = getPixelNeighborhood(cachedImageDataRef.current, imgX, imgY, 2);
          setMatrix(hood);
        } else {
          setMatrix(null);
        }
      }

      // Record position relative to container
      const containerRect = container.getBoundingClientRect();
      setClientPos({
        x: clientX - containerRect.left,
        y: clientY - containerRect.top,
      });
    };

    const handlePointerLeave = () => {
      setProbe(null);
      setMatrix(null);
      setClientPos(null);
    };

    container.addEventListener("pointermove", handlePointerMove);
    container.addEventListener("pointerleave", handlePointerLeave);

    return () => {
      container.removeEventListener("pointermove", handlePointerMove);
      container.removeEventListener("pointerleave", handlePointerLeave);
      cachedImageDataRef.current = null;
      setProbe(null);
      setMatrix(null);
      setClientPos(null);
    };
  }, [active, containerRef, imageRef, showLoupe, imageSrc]);

  if (!active || !probe) return null;

  return (
    <>
      {/* Real-time floating probe pill (pinned cleanly to bottom of image container) */}
      <div className="absolute bottom-2 left-2 right-2 z-30 pointer-events-none flex items-center justify-between px-2.5 py-1.5 rounded bg-white/95 dark:bg-gray-900/95 border border-gray-200 dark:border-gray-700 shadow-md backdrop-blur-xs text-[11px] font-mono text-gray-700 dark:text-gray-300">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-900 dark:text-gray-100">
            X:{probe.x} Y:{probe.y}
          </span>
          <span className="text-gray-400 dark:text-gray-500">|</span>
          <span className="flex items-center gap-1">
            <span
              className="w-3 h-3 rounded-xs border border-gray-300 dark:border-gray-600 inline-block"
              style={{ backgroundColor: probe.hex }}
            />
            <span>
              RGB({probe.r}, {probe.g}, {probe.b})
            </span>
          </span>
          <span className="text-gray-400 dark:text-gray-500">|</span>
          <span className="text-indigo-600 dark:text-indigo-400 font-medium">
            Luma: {probe.luma}
          </span>
        </div>
        <button
          type="button"
          onClick={() => setShowLoupe((prev) => !prev)}
          className="pointer-events-auto ml-2 px-1.5 py-0.5 rounded text-[10px] bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 cursor-pointer transition-colors"
          title="Toggle 5x5 neighborhood matrix"
        >
          {showLoupe ? "Hide Grid" : "5x5 Grid"}
        </button>
      </div>

      {/* Floating 5x5 pixel neighborhood matrix (ImageJ Pixel Inspection Tool) */}
      {showLoupe && matrix && clientPos && (
        <div
          className="absolute z-40 pointer-events-none bg-white/95 dark:bg-gray-900/95 border border-gray-200 dark:border-gray-700 p-1.5 rounded shadow-lg backdrop-blur-xs font-mono text-[9px] -translate-x-1/2 -translate-y-full mb-3"
          style={{
            left: `${Math.max(60, Math.min(clientPos.x, 260))}px`,
            top: `${Math.max(70, clientPos.y - 12)}px`,
          }}
        >
          <div className="grid grid-cols-5 gap-0.5 text-center">
            {matrix.map((row, rIdx) =>
              row.map((cell, cIdx) => {
                const isCenter = rIdx === 2 && cIdx === 2;
                return (
                  <div
                    key={`${rIdx}-${cIdx}`}
                    className={`w-5 h-5 flex items-center justify-center rounded-xs transition-colors ${
                      isCenter
                        ? "bg-indigo-600 text-white font-bold ring-1 ring-indigo-400"
                        : cell
                          ? "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
                          : "bg-gray-50 dark:bg-gray-900 text-gray-400 opacity-40"
                    }`}
                    style={
                      cell && !isCenter
                        ? {
                            backgroundColor: `rgba(${cell.r}, ${cell.g}, ${cell.b}, 0.25)`,
                          }
                        : undefined
                    }
                    title={cell ? `(${cell.x}, ${cell.y}): Luma ${cell.luma}` : "Out of bounds"}
                  >
                    {cell ? Math.round(cell.luma) : "·"}
                  </div>
                );
              }),
            )}
          </div>
        </div>
      )}
    </>
  );
}
