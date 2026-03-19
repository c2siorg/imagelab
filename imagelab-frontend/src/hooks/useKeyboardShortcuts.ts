import { useEffect } from "react";
import * as Blockly from "blockly";

interface ShortcutHandlers {
  onRun: () => void;
  onDownload: () => void;
  onUndo: () => void;
  onRedo: () => void;
  workspace: Blockly.WorkspaceSvg | null;
}

function isTypingInBlockly(): boolean {
  const active = document.activeElement;
  if (!active) return false;
  const tag = active.tagName.toLowerCase();
  // Blockly uses <input> and <textarea> for field editors
  if (tag === "input" || tag === "textarea") return true;
  // contenteditable divs used by some Blockly fields
  if ((active as HTMLElement).isContentEditable) return true;
  return false;
}

export function useKeyboardShortcuts({
  onRun,
  onDownload,
  onUndo,
  onRedo,
  workspace,
}: ShortcutHandlers) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const meta = e.ctrlKey || e.metaKey;

      // Delete/Backspace: remove selected Blockly block (not when typing)
      if ((e.key === "Delete" || e.key === "Backspace") && !isTypingInBlockly()) {
        if (workspace) {
          const selected = Blockly.common.getSelected();
          if (selected && selected instanceof Blockly.BlockSvg) {
            e.preventDefault();
            selected.dispose(true, true);
            return;
          }
        }
      }

      if (!meta) return;

      switch (e.key) {
        case "Enter":
          e.preventDefault();
          onRun();
          break;
        case "s":
        case "S":
          e.preventDefault();
          onDownload();
          break;
        case "z":
        case "Z":
          if (!isTypingInBlockly()) {
            e.preventDefault();
            if (e.shiftKey) {
              onRedo();
            } else {
              onUndo();
            }
          }
          break;
        case "y":
        case "Y":
          if (!isTypingInBlockly()) {
            e.preventDefault();
            onRedo();
          }
          break;
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onRun, onDownload, onUndo, onRedo, workspace]);
}
