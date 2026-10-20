/**
 * useCanvasRoi: Custom React Hook for Interactive Region of Interest (ROI) Annotation
 *
 * Encapsulates gesture pointer physics, 8-directional handle resizing, aspect ratio constraints,
 * coordinate projections, keyboard nudging, and direct synchronization with Blockly blocks.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import * as Blockly from "blockly";
import {
  applyAspectRatio,
  clampRoiBox,
  normalizeBoundingBox,
  resizeBoundingBox,
  translateBoundingBox,
  viewportToImageCoordinates,
  type BoundingBox,
  type Dimensions,
  type Point,
  type ResizeHandle,
} from "../utils/roiCoordinates";

export interface UseCanvasRoiOptions {
  naturalDimensions: Dimensions;
  containerRef: React.RefObject<HTMLDivElement | null>;
  imageRef?: React.RefObject<HTMLImageElement | null>;
  initialBox?: BoundingBox | null;
  onBoxChange?: (box: BoundingBox | null) => void;
}

export type InteractionMode = "idle" | "creating" | "resizing" | "moving";

export interface ApplyToBlockResult {
  success: boolean;
  blockType?: string;
  message: string;
}

export function useCanvasRoi({
  naturalDimensions,
  containerRef,
  imageRef,
  initialBox = null,
  onBoxChange,
}: UseCanvasRoiOptions) {
  const [roiBox, setRoiBoxInternal] = useState<BoundingBox | null>(initialBox);
  const [aspectRatio, setAspectRatio] = useState<number | null>(null);
  const [interactionMode, setInteractionMode] = useState<InteractionMode>("idle");
  const [activeHandle, setActiveHandle] = useState<ResizeHandle | null>(null);

  // References for drag calculation to avoid closure staleness
  const dragStartPointRef = useRef<Point>({ x: 0, y: 0 });
  const boxAtStartRef = useRef<BoundingBox | null>(null);

  const setRoiBox = useCallback(
    (newBox: BoundingBox | null) => {
      setRoiBoxInternal(newBox);
      onBoxChange?.(newBox);
    },
    [onBoxChange],
  );

  /**
   * Translates client pointer coordinates into image pixel space using container bounds
   */
  const getPointerImageCoordinates = useCallback(
    (clientX: number, clientY: number): Point => {
      const target = imageRef?.current ?? containerRef.current;
      if (!target) return { x: 0, y: 0 };

      const rect = target.getBoundingClientRect();
      const viewportPoint: Point = {
        x: clientX - rect.left,
        y: clientY - rect.top,
      };

      const displayDims: Dimensions = {
        width: rect.width,
        height: rect.height,
      };

      return viewportToImageCoordinates(viewportPoint, displayDims, naturalDimensions);
    },
    [containerRef, imageRef, naturalDimensions],
  );

  /**
   * Begins a new ROI creation by dragging across the canvas
   */
  const startCreation = useCallback(
    (clientX: number, clientY: number) => {
      const startPoint = getPointerImageCoordinates(clientX, clientY);
      dragStartPointRef.current = startPoint;
      boxAtStartRef.current = {
        x1: startPoint.x,
        y1: startPoint.y,
        x2: startPoint.x,
        y2: startPoint.y,
      };
      setInteractionMode("creating");
      setRoiBox({
        x1: startPoint.x,
        y1: startPoint.y,
        x2: startPoint.x,
        y2: startPoint.y,
      });
    },
    [getPointerImageCoordinates, setRoiBox],
  );

  /**
   * Begins moving an existing ROI box
   */
  const startMoving = useCallback(
    (clientX: number, clientY: number) => {
      if (!roiBox) return;
      dragStartPointRef.current = getPointerImageCoordinates(clientX, clientY);
      boxAtStartRef.current = { ...roiBox };
      setInteractionMode("moving");
    },
    [getPointerImageCoordinates, roiBox],
  );

  /**
   * Begins resizing an existing ROI box via one of the 8 compass handles
   */
  const startResizing = useCallback(
    (handle: ResizeHandle, clientX: number, clientY: number) => {
      if (!roiBox) return;
      dragStartPointRef.current = getPointerImageCoordinates(clientX, clientY);
      boxAtStartRef.current = { ...roiBox };
      setActiveHandle(handle);
      setInteractionMode("resizing");
    },
    [getPointerImageCoordinates, roiBox],
  );

  /**
   * Global pointer move listener during active drag operations
   */
  useEffect(() => {
    if (interactionMode === "idle") return;

    const handlePointerMove = (e: PointerEvent) => {
      const currentPoint = getPointerImageCoordinates(e.clientX, e.clientY);

      if (interactionMode === "creating") {
        let candidate = normalizeBoundingBox(dragStartPointRef.current, currentPoint);
        if (aspectRatio !== null && aspectRatio > 0) {
          candidate = applyAspectRatio(candidate, aspectRatio, "nw", naturalDimensions);
        }
        setRoiBox(clampRoiBox(candidate, naturalDimensions));
      } else if (interactionMode === "moving" && boxAtStartRef.current) {
        const delta: Point = {
          x: currentPoint.x - dragStartPointRef.current.x,
          y: currentPoint.y - dragStartPointRef.current.y,
        };
        const candidate = translateBoundingBox(boxAtStartRef.current, delta, naturalDimensions);
        setRoiBox(candidate);
      } else if (interactionMode === "resizing" && boxAtStartRef.current && activeHandle) {
        let candidate = resizeBoundingBox(
          boxAtStartRef.current,
          activeHandle,
          currentPoint,
          naturalDimensions,
        );
        if (aspectRatio !== null && aspectRatio > 0) {
          candidate = applyAspectRatio(candidate, aspectRatio, activeHandle, naturalDimensions);
        }
        setRoiBox(clampRoiBox(candidate, naturalDimensions));
      }
    };

    const handlePointerUp = () => {
      setInteractionMode("idle");
      setActiveHandle(null);
      boxAtStartRef.current = null;
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", handlePointerUp);

    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", handlePointerUp);
    };
  }, [
    activeHandle,
    aspectRatio,
    getPointerImageCoordinates,
    interactionMode,
    naturalDimensions,
    setRoiBox,
  ]);

  /**
   * Nudges the bounding box using keyboard arrow keys
   */
  const nudgeRoi = useCallback(
    (dx: number, dy: number) => {
      if (!roiBox) return;
      const translated = translateBoundingBox(roiBox, { x: dx, y: dy }, naturalDimensions);
      setRoiBox(translated);
    },
    [naturalDimensions, roiBox, setRoiBox],
  );

  /**
   * Resets and clears the active ROI selection
   */
  const clearRoi = useCallback(() => {
    setRoiBox(null);
    setInteractionMode("idle");
    setActiveHandle(null);
  }, [setRoiBox]);

  /**
   * Automatically applies the current ROI coordinates to an active or compatible Blockly block
   */
  const applyRoiToBlock = useCallback(
    (workspace: Blockly.WorkspaceSvg | null): ApplyToBlockResult => {
      if (!roiBox) {
        return { success: false, message: "No ROI bounding box selected on image" };
      }

      if (!workspace) {
        return { success: false, message: "Workspace not initialized" };
      }

      // Check if a block is currently selected in Blockly
      let selectedBlock: Blockly.BlockSvg | null = null;
      try {
        selectedBlock = (Blockly.common?.getSelected?.() ?? null) as Blockly.BlockSvg | null;
      } catch {
        selectedBlock = null;
      }

      const targetBlocks = selectedBlock
        ? [selectedBlock]
        : workspace.getAllBlocks(false).filter((b) => {
            return b.type === "geometric_cropimage" || b.type === "drawingoperations_drawrectangle";
          });

      if (targetBlocks.length === 0) {
        return {
          success: false,
          message: "No Crop or Rectangle blocks found in workspace. Add a Crop Image block first.",
        };
      }

      const target = targetBlocks[0];

      const normX1 = Math.round(Math.min(roiBox.x1, roiBox.x2));
      const normY1 = Math.round(Math.min(roiBox.y1, roiBox.y2));
      const normX2 = Math.round(Math.max(roiBox.x1, roiBox.x2));
      const normY2 = Math.round(Math.max(roiBox.y1, roiBox.y2));

      const setBlockFields = (fields: Record<string, string>) => {
        const hasEvents = typeof Blockly.Events?.setGroup === "function";
        if (hasEvents) {
          Blockly.Events.setGroup(true);
        }
        try {
          for (const [key, value] of Object.entries(fields)) {
            target.setFieldValue(value, key);
          }
        } finally {
          if (hasEvents) {
            Blockly.Events.setGroup(false);
          }
        }
      };

      if (target.type === "geometric_cropimage") {
        setBlockFields({
          x1: String(normX1),
          y1: String(normY1),
          x2: String(normX2),
          y2: String(normY2),
        });
        return {
          success: true,
          blockType: "Crop Image",
          message: `Applied coordinates (${normX1}, ${normY1}) to (${normX2}, ${normY2}) to Crop Image block`,
        };
      }

      if (target.type === "drawingoperations_drawrectangle") {
        setBlockFields({
          starting_point_x: String(normX1),
          starting_point_y: String(normY1),
          ending_point_x: String(normX2),
          ending_point_y: String(normY2),
        });
        return {
          success: true,
          blockType: "Draw Rectangle",
          message: `Applied coordinates to Draw Rectangle block`,
        };
      }

      return {
        success: false,
        message: `Selected block '${target.type}' does not accept rectangular ROI coordinates.`,
      };
    },
    [roiBox],
  );

  return {
    roiBox,
    setRoiBox,
    aspectRatio,
    setAspectRatio,
    interactionMode,
    activeHandle,
    startCreation,
    startMoving,
    startResizing,
    nudgeRoi,
    clearRoi,
    applyRoiToBlock,
  };
}
