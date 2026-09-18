import { useState, useEffect } from "react";
import type { RefObject } from "react";
import { usePipelineStore } from "../store/pipelineStore";
import { getImageFormatFromMimeType } from "../utils/imageData";

interface UseWorkspaceDropOptions {
  /** Ref to the drop zone container element matching DropOverlay's bounds */
  dropZoneRef?: RefObject<HTMLDivElement | null>;
  /** @deprecated Use dropZoneRef instead */
  containerRef?: RefObject<HTMLDivElement | null>;
  enabled?: boolean;
}

export function useWorkspaceDrop({
  dropZoneRef,
  containerRef,
  enabled = true,
}: UseWorkspaceDropOptions) {
  const targetRef = dropZoneRef ?? containerRef;
  const [isDragOver, setIsDragOver] = useState(false);
  const { setOriginalImage } = usePipelineStore();

  useEffect(() => {
    const target = targetRef?.current;
    if (!target || !enabled) return;

    const handleDragEnter = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();

      // Only show overlay if dropping files (not text or other data)
      if (e.dataTransfer?.types.includes("Files")) {
        setIsDragOver(true);
      }
    };

    const handleDragOver = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();

      // Set dropEffect to indicate this is a valid drop target
      if (e.dataTransfer) {
        e.dataTransfer.dropEffect = "copy";
      }
    };

    const handleDragLeave = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();

      // Only hide overlay if leaving the drop zone container itself (not child elements)
      if (!e.relatedTarget || !target.contains(e.relatedTarget as Node)) {
        setIsDragOver(false);
      }
    };

    const handleDrop = (e: DragEvent) => {
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
    };

    target.addEventListener("dragenter", handleDragEnter);
    target.addEventListener("dragover", handleDragOver);
    target.addEventListener("dragleave", handleDragLeave);
    target.addEventListener("drop", handleDrop);

    return () => {
      target.removeEventListener("dragenter", handleDragEnter);
      target.removeEventListener("dragover", handleDragOver);
      target.removeEventListener("dragleave", handleDragLeave);
      target.removeEventListener("drop", handleDrop);
    };
  }, [targetRef, enabled, setOriginalImage]);

  return { isDragOver };
}
