import { useEffect, useCallback } from "react";
import { usePipelineStore } from "../store/pipelineStore";
import { getImageFormatFromMimeType } from "../utils/imageData";

interface UseClipboardPasteOptions {
  enabled?: boolean;
}

export function useClipboardPaste({ enabled = true }: UseClipboardPasteOptions = {}) {
  const { setOriginalImage } = usePipelineStore();

  const handlePaste = useCallback(
    (e: ClipboardEvent) => {
      if (!enabled) return;

      // Don't hijack paste if user is focused on a text input or contenteditable element
      const target = e.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable ||
        target.closest("[contenteditable]") ||
        // Don't hijack paste inside Blockly field editors
        target.closest(".blocklyWidgetDiv") ||
        target.closest(".blocklyDropDownDiv")
      ) {
        return;
      }

      const items = e.clipboardData?.items;
      if (!items) return;

      // Find the first image item in the clipboard
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.type.startsWith("image/")) {
          e.preventDefault(); // Prevent default paste behavior only if we found an image

          const blob = item.getAsFile();
          if (!blob) continue;

          const format = getImageFormatFromMimeType(blob.type);
          const reader = new FileReader();

          reader.onload = () => {
            const dataUrl = reader.result as string;
            const base64 = dataUrl.split(",")[1];
            if (base64) {
              // Generate a descriptive filename for pasted images
              const timestamp = new Date().toISOString().split("T")[0];
              const filename = `pasted-image-${timestamp}.${format}`;
              setOriginalImage(base64, format, filename);
            }
          };

          reader.onerror = () => {
            console.error("Failed to read pasted image");
          };

          reader.readAsDataURL(blob);
          break; // Only process the first image
        }
      }
    },
    [enabled, setOriginalImage],
  );

  useEffect(() => {
    if (!enabled) return;

    document.addEventListener("paste", handlePaste);

    return () => {
      document.removeEventListener("paste", handlePaste);
    };
  }, [enabled, handlePaste]);
}
