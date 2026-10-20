/**
 * ImageComparisonModal Component
 *
 * Fullscreen high-definition comparison dialog allowing in-depth inspection of
 * subtle image processing changes across Split, 2-Up Side-by-Side, Difference Heatmaps,
 * and Hold/Blink modes without screen space limitations.
 */

import { useEffect } from "react";
import { X, Layers } from "lucide-react";
import ImageComparisonSlider from "./ImageComparisonSlider";

export interface ImageComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  originalSrc: string;
  processedSrc: string;
  originalLabel?: string;
  processedLabel?: string;
}

export default function ImageComparisonModal({
  isOpen,
  onClose,
  originalSrc,
  processedSrc,
  originalLabel = "Original",
  processedLabel = "Processed",
}: ImageComparisonModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "auto";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 sm:p-6"
      onClick={onClose}
    >
      <div
        className="w-full max-w-6xl h-[90vh] bg-white dark:bg-gray-800 rounded-xl shadow-2xl flex flex-col overflow-hidden border border-gray-200 dark:border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="h-10 px-4 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2">
            <Layers size={16} className="text-indigo-600 dark:text-indigo-400" />
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
              Comparison Inspector
            </h3>
            <span className="text-xs px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 font-mono">
              {originalLabel} vs {processedLabel}
            </span>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-md text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors cursor-pointer"
            title="Close dialog (Escape)"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body: High-resolution Comparison Viewport */}
        <div className="flex-1 min-h-0 relative">
          <ImageComparisonSlider
            originalSrc={originalSrc}
            processedSrc={processedSrc}
            originalLabel={originalLabel}
            processedLabel={processedLabel}
            onClose={onClose}
          />
        </div>
      </div>
    </div>
  );
}
