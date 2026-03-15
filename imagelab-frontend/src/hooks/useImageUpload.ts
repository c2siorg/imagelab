import { useCallback, useEffect, useRef, useState } from "react";
import * as Blockly from "blockly";
import { usePipelineStore } from "../store/pipelineStore";

function normaliseFormat(mimeType: string): string {
  const sub = mimeType.split("/")[1] ?? "png";
  if (sub === "jpg") return "jpeg";
  if (sub === "tif") return "tiff";
  return sub;
}

export function loadImageFile(file: File, onLoaded?: (filename: string) => void): Promise<void> {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith("image/")) {
      resolve();
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      const base64 = dataUrl.split(",")[1];
      usePipelineStore.getState().setOriginalImage(base64, normaliseFormat(file.type));
      onLoaded?.(file.name);
      resolve();
    };
    reader.onerror = () => reject(new Error("Failed to read file"));
    reader.readAsDataURL(file);
  });
}

function updateReadImageLabel(workspace: Blockly.WorkspaceSvg, filename: string) {
  const blocks = workspace.getBlocksByType("basic_readimage", false);
  if (blocks.length > 0) {
    blocks[0].getField("filename_label")?.setValue(filename);
  }
}

export function useImageDropAndPaste(
  dropTargetRef: React.RefObject<HTMLElement | null>,
  workspace: Blockly.WorkspaceSvg | null,
) {
  const [isDragging, setIsDragging] = useState(false);
  const dragCounter = useRef(0);

  const handleFile = useCallback(
    (file: File) => {
      loadImageFile(file, (filename) => {
        if (workspace) updateReadImageLabel(workspace, filename);
      });
    },
    [workspace],
  );

  useEffect(() => {
    const el = dropTargetRef.current;
    if (!el) return;

    const onDragEnter = (e: DragEvent) => {
      e.preventDefault();
      dragCounter.current += 1;
      if (dragCounter.current === 1) setIsDragging(true);
    };
    const onDragOver = (e: DragEvent) => {
      e.preventDefault();
      if (e.dataTransfer) e.dataTransfer.dropEffect = "copy";
    };
    const onDragLeave = (e: DragEvent) => {
      e.preventDefault();
      dragCounter.current -= 1;
      if (dragCounter.current === 0) setIsDragging(false);
    };
    const onDrop = (e: DragEvent) => {
      e.preventDefault();
      dragCounter.current = 0;
      setIsDragging(false);
      const file = e.dataTransfer?.files[0];
      if (file) handleFile(file);
    };

    el.addEventListener("dragenter", onDragEnter);
    el.addEventListener("dragover", onDragOver);
    el.addEventListener("dragleave", onDragLeave);
    el.addEventListener("drop", onDrop);
    return () => {
      el.removeEventListener("dragenter", onDragEnter);
      el.removeEventListener("dragover", onDragOver);
      el.removeEventListener("dragleave", onDragLeave);
      el.removeEventListener("drop", onDrop);
    };
  }, [dropTargetRef, handleFile]);

  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      for (const item of items) {
        if (item.kind === "file" && item.type.startsWith("image/")) {
          const file = item.getAsFile();
          if (file) {
            handleFile(file);
            break;
          }
        }
      }
    };
    document.addEventListener("paste", onPaste);
    return () => document.removeEventListener("paste", onPaste);
  }, [handleFile]);

  return { isDragging };
}
