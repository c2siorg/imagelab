import { useEffect, useRef } from "react";
import { AlertTriangle, X } from "lucide-react";
import type { ValidationWarning } from "../utils/validatePipelineGraph";

interface ValidationWarningModalProps {
  isOpen: boolean;
  warnings: ValidationWarning[];
  onRunAnyway: () => void;
  onCancel: () => void;
}

export default function ValidationWarningModal({
  isOpen,
  warnings,
  onRunAnyway,
  onCancel,
}: ValidationWarningModalProps) {
  const runAnywayButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) {
      // Focus the run anyway button when dialog opens
      runAnywayButtonRef.current?.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onCancel();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 backdrop-blur-xs"
      onClick={onCancel}
      role="presentation"
    >
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="validation-dialog-title"
        aria-describedby="validation-dialog-description"
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden border border-gray-200 dark:border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 bg-amber-50 dark:bg-amber-950/20">
          <div className="flex items-center gap-2">
            <AlertTriangle size={18} className="text-amber-600 dark:text-amber-500" />
            <h2
              id="validation-dialog-title"
              className="text-sm font-semibold text-gray-800 dark:text-gray-100"
            >
              Pipeline Validation Warnings
            </h2>
          </div>
          <button
            type="button"
            onClick={onCancel}
            className="p-1 rounded hover:bg-amber-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
            title="Close"
            aria-label="Close"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 max-h-96 overflow-y-auto">
          <p
            id="validation-dialog-description"
            className="text-sm text-gray-600 dark:text-gray-300 mb-4"
          >
            {warnings.length === 1
              ? "We found a potential issue with your pipeline:"
              : `We found ${warnings.length} potential issues with your pipeline:`}
          </p>

          <ul className="space-y-3">
            {warnings.map((warning, index) => (
              <li
                key={index}
                className="flex gap-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-950/10 border border-amber-200 dark:border-amber-900/30"
              >
                <AlertTriangle
                  size={16}
                  className="text-amber-600 dark:text-amber-500 flex-shrink-0 mt-0.5"
                  aria-hidden="true"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-700 dark:text-gray-200 break-words">
                    {warning.message}
                  </p>
                  {warning.nodeId && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Block ID: {warning.nodeId}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-4 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/10 border border-blue-200 dark:border-blue-900/30">
            <p className="text-xs text-gray-600 dark:text-gray-300">
              <strong className="text-gray-800 dark:text-gray-100">Note:</strong> These warnings
              help identify common mistakes before running your pipeline. You can still run the
              pipeline if you believe the configuration is correct, but it may fail during
              execution.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-2 px-5 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-xs font-medium text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          >
            Cancel and Fix
          </button>
          <button
            ref={runAnywayButtonRef}
            type="button"
            onClick={onRunAnyway}
            className="px-4 py-2 text-xs font-medium text-white bg-amber-600 hover:bg-amber-700 dark:bg-amber-600 dark:hover:bg-amber-700 rounded-lg transition-colors"
          >
            Run Anyway
          </button>
        </div>
      </div>
    </div>
  );
}
