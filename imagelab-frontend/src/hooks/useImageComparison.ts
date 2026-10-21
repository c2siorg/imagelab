/**
 * useImageComparison: Custom React Hook for Before/After Visual Comparisons
 *
 * Manages curtain split slider position, horizontal/vertical orientations, side-by-side sync,
 * onion-skin opacity blending, and difference heatmap colormaps.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import type { ColormapType } from "../utils/imageDiff";

export type ComparisonMode = "split" | "side-by-side" | "difference" | "onion-skin";
export type SplitOrientation = "horizontal" | "vertical";

export interface UseImageComparisonOptions {
  initialMode?: ComparisonMode;
  initialPosition?: number;
  initialOrientation?: SplitOrientation;
}

export function useImageComparison({
  initialMode = "split",
  initialPosition = 50,
  initialOrientation = "horizontal",
}: UseImageComparisonOptions = {}) {
  const [mode, setMode] = useState<ComparisonMode>(initialMode);
  const [position, setPositionInternal] = useState<number>(initialPosition);
  const [orientation, setOrientation] = useState<SplitOrientation>(initialOrientation);
  const [blendOpacity, setBlendOpacity] = useState<number>(0.5);
  const [colormap, setColormap] = useState<ColormapType>("thermal");
  const [isDraggingSlider, setIsDraggingSlider] = useState<boolean>(false);

  const containerRef = useRef<HTMLDivElement | null>(null);

  /**
   * Sets slider position clamped strictly between 0% and 100%
   */
  const setPosition = useCallback((pos: number) => {
    const clamped = Math.max(0, Math.min(100, Math.round(pos * 10) / 10));
    setPositionInternal(clamped);
  }, []);

  /**
   * Calculates slider percentage from pointer coordinates relative to the container
   */
  const updatePositionFromPointer = useCallback(
    (clientX: number, clientY: number) => {
      const container = containerRef.current;
      if (!container) return;

      const rect = container.getBoundingClientRect();

      if (orientation === "horizontal") {
        const offset = clientX - rect.left;
        const percentage = (offset / rect.width) * 100;
        setPosition(percentage);
      } else {
        const offset = clientY - rect.top;
        const percentage = (offset / rect.height) * 100;
        setPosition(percentage);
      }
    },
    [orientation, setPosition],
  );

  /**
   * Starts dragging the comparison slider
   */
  const startDragging = useCallback(
    (clientX: number, clientY: number) => {
      setIsDraggingSlider(true);
      updatePositionFromPointer(clientX, clientY);
    },
    [updatePositionFromPointer],
  );

  /**
   * Global pointer tracking during active slider dragging
   */
  useEffect(() => {
    if (!isDraggingSlider) return;

    const handlePointerMove = (e: PointerEvent) => {
      updatePositionFromPointer(e.clientX, e.clientY);
    };

    const handlePointerUp = () => {
      setIsDraggingSlider(false);
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", handlePointerUp);

    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", handlePointerUp);
    };
  }, [isDraggingSlider, updatePositionFromPointer]);

  /**
   * Keyboard accessibility for slider adjustments
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      let step = 1;
      if (e.shiftKey) step = 5;

      if (orientation === "horizontal") {
        if (e.key === "ArrowLeft") {
          e.preventDefault();
          setPosition(position - step);
        } else if (e.key === "ArrowRight") {
          e.preventDefault();
          setPosition(position + step);
        }
      } else {
        if (e.key === "ArrowUp") {
          e.preventDefault();
          setPosition(position - step);
        } else if (e.key === "ArrowDown") {
          e.preventDefault();
          setPosition(position + step);
        }
      }

      if (e.key === "Home") {
        e.preventDefault();
        setPosition(0);
      } else if (e.key === "End") {
        e.preventDefault();
        setPosition(100);
      }
    },
    [orientation, position, setPosition],
  );

  const toggleOrientation = useCallback(() => {
    setOrientation((prev) => (prev === "horizontal" ? "vertical" : "horizontal"));
  }, []);

  return {
    mode,
    setMode,
    position,
    setPosition,
    orientation,
    setOrientation,
    toggleOrientation,
    blendOpacity,
    setBlendOpacity,
    colormap,
    setColormap,
    isDraggingSlider,
    containerRef,
    startDragging,
    handleKeyDown,
  };
}
