import { useEffect } from "react";

interface ConfirmDialogProps {
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({ message, onConfirm, onCancel }: ConfirmDialogProps) {
  // Close on Escape key — mirrors SharePipelineModal pattern
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onCancel]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={onCancel}
      role="presentation"
    >
      <div
        role="alertdialog"
        aria-modal="true"
        aria-describedby="confirm-dialog-message"
        className="bg-white rounded-xl shadow-2xl w-full max-w-sm mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Body */}
        <div className="px-5 py-5">
          <p id="confirm-dialog-message" className="text-sm text-gray-700 leading-relaxed">
            {message}
          </p>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 px-5 pb-4">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-1.5 rounded-lg text-sm font-medium border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="px-4 py-1.5 rounded-lg text-sm font-medium text-white bg-indigo-500 hover:bg-indigo-600 transition-colors"
          >
            OK
          </button>
        </div>
      </div>
    </div>
  );
}
