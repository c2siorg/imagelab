import { useState, useCallback, useEffect } from "react";
import type { RefObject } from "react";
import { usePipelineStore } from "../store/pipelineStore";
import { getImageFormatFromMimeType } from "../utils/imageData";

interface UseWorkspaceDropOptions {
  containerRef: RefObject<HTMLDivElement>;
  enabled?: boolean;
}

export function useWorkspaceDrop({ containerRef, enabled = true }: UseWorkspaceDropOptions) {
  const [isDragOver, setIsDragOver] = useState(false);
  const { setOriginalImage } = usePipelineStore();

  const handleDragEnter = useCallback(
    (e: DragEvent) => {
      if (!enabled) return;
      e.preventDefault();
      e.stopPropagation();

      // Only show overlay if dropping files (not text or other data)
      if (e.dataTransfer?.types.includes("Files")) {
        setIsDragOver(true);
      }
    },
    [enabled],
  );

  const handleDragOver = useCallback(
    (e: DragEvent) => {
      if (!enabled) return;
      e.preventDefault();
      e.stopPropagation();

      // Set dropEffect to indicate this is a valid drop target
      if (e.dataTransfer) {
        e.dataTransfer.dropEffect = "copy";
      }
    },
    [enabled],
  );

  const handleDragLeave = useCallback(
    (e: DragEvent) => {
      if (!enabled) return;
      e.preventDefault();
      e.stopPropagation();

      // Only hide overlay if leaving the container itself (not child elements)
      const target = e.target as HTMLElement;
      const container = containerRef.current;
      if (container && (target === container || !container.contains(e.relatedTarget as Node))) {
        setIsDragOver(false);
      }
    },
    [enabled, containerRef],
  );

  const handleDrop = useCallback(
    (e: DragEvent) => {
      if (!enabled) return;
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);

      const files = e.dataTransfer?.files;
      if (!files || files.length === 0) return;

      // Take the first image file
      const imageFile = Array.from(files).find((file) => file.type.startsWith("image/"));

      if (!imageFile) {
        console.warn("No image file found in drop");
        return;
      }

      const format = getImageFormatFromMimeType(imageFile.type);
      const reader = new FileReader();

      reader.onload = () => {
        const dataUrl = reader.result as string;
        const base64 = dataUrl.split(",")[1];
        if (base64) {
          setOriginalImage(base64, format, imageFile.name);
        }
      };

      reader.onerror = () => {
        console.error("Failed to read dropped image file");
      };

      reader.readAsDataURL(imageFile);
    },
    [enabled, setOriginalImage],
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !enabled) return;

    container.addEventListener("dragenter", handleDragEnter);
    container.addEventListener("dragover", handleDragOver);
    container.addEventListener("dragleave", handleDragLeave);
    container.addEventListener("drop", handleDrop);

    return () => {
      container.removeEventListener("dragenter", handleDragEnter);
      container.removeEventListener("dragover", handleDragOver);
      container.removeEventListener("dragleave", handleDragLeave);
      container.removeEventListener("drop", handleDrop);
    };
  }, [containerRef, enabled, handleDragEnter, handleDragOver, handleDragLeave, handleDrop]);

  return { isDragOver };
}
