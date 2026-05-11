import { X, Keyboard } from "lucide-react";
import { useEffect, useRef } from "react";

interface KeyboardShortcutsModalProps {
  onClose: () => void;
}

const isMac =
  typeof navigator !== "undefined" && /mac/i.test(navigator.platform || navigator.userAgent);
const mod = isMac ? "⌘" : "Ctrl";

const SHORTCUTS = [
  {
    category: "Pipeline",
    items: [
      { keys: [mod, "Enter"], description: "Run pipeline" },
      { keys: [mod, "S"], description: "Download processed image" },
    ],
  },
  {
    category: "Edit",
    items: [
      { keys: [mod, "Z"], description: "Undo" },
      { keys: [mod, "⇧Z"], description: "Redo" },
      { keys: [mod, "Y"], description: "Redo (alternative)" },
      { keys: ["Delete"], description: "Remove selected block" },
      { keys: ["Backspace"], description: "Remove selected block" },
    ],
  },
  {
    category: "Help",
    items: [{ keys: ["⇧", "?"], description: "Open this shortcuts panel" }],
  },
];

export default function KeyboardShortcutsModal({ onClose }: KeyboardShortcutsModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    dialogRef.current?.focus();
  }, []);

  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={onClose}
      role="none"
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="shortcuts-modal-title"
        tabIndex={-1}
        className="bg-white rounded-xl shadow-2xl w-full max-w-sm mx-4 overflow-hidden outline-none"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Keyboard size={16} className="text-gray-500" />
            <h2 id="shortcuts-modal-title" className="text-sm font-semibold text-gray-800">
              Keyboard Shortcuts
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
            title="Close"
            aria-label="Close"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>

        <div className="p-5 space-y-5">
          {SHORTCUTS.map((group) => (
            <div key={group.category}>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-2">
                {group.category}
              </div>
              <div className="space-y-2">
                {group.items.map((shortcut, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-xs text-gray-600">{shortcut.description}</span>
                    <div className="flex items-center gap-1">
                      {shortcut.keys.map((key, ki) => (
                        <span
                          key={ki}
                          className="inline-flex items-center justify-center min-w-[1.5rem] h-6 px-1.5 rounded bg-gray-100 border border-gray-300 text-[11px] font-medium text-gray-700 font-mono shadow-sm"
                        >
                          {key}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
