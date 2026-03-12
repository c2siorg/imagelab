import { AlertTriangle, X, Play } from "lucide-react";
import type { ValidationWarning } from "../utils/pipelineValidation";

interface PipelineWarningsModalProps {
  warnings: ValidationWarning[];
  onRunAnyway: () => void;
  onCancel: () => void;
}

export default function PipelineWarningsModal({
  warnings,
  onRunAnyway,
  onCancel,
}: PipelineWarningsModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={onCancel}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Pipeline Warnings"
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <AlertTriangle size={18} className="text-amber-500" />
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
              Pipeline Warnings
            </h2>
          </div>
          <button
            type="button"
            onClick={onCancel}
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
            title="Close"
            aria-label="Close"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>

        {/* Warnings list */}
        <div className="p-5 space-y-3 max-h-72 overflow-y-auto">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            The following issues were detected before running. You can fix them or run anyway.
          </p>
          <ul className="space-y-2">
            {warnings.map((w, idx) => (
              <li
                key={idx}
                className="flex gap-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800"
              >
                <AlertTriangle
                  size={14}
                  className="text-amber-500 flex-shrink-0 mt-0.5"
                  aria-hidden="true"
                />
                <div className="flex flex-col gap-0.5">
                  {w.step > 0 && (
                    <span className="text-[10px] font-semibold text-amber-600 dark:text-amber-400 uppercase tracking-wide">
                      Step {w.step}
                    </span>
                  )}
                  <span className="text-xs text-amber-800 dark:text-amber-200">{w.message}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Actions */}
        <div className="flex gap-2 px-5 py-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 py-2 px-3 rounded-lg text-sm font-medium border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onRunAnyway}
            className="flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-sm font-medium text-white bg-indigo-500 hover:bg-indigo-600 transition-colors"
          >
            <Play size={14} aria-hidden="true" />
            Run Anyway
          </button>
        </div>
      </div>
    </div>
  );
}
