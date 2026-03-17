import { useRef, useCallback, useEffect } from "react";
import * as Blockly from "blockly";
import { SINGLETON_BLOCK_TYPES, isSingletonBlockPresent } from "../utils/blockLimits";

const DRAG_THRESHOLD = 5;

function createSyntheticPointerEvent(e: MouseEvent): PointerEvent {
  return new PointerEvent("pointermove", {
    clientX: e.clientX,
    clientY: e.clientY,
    bubbles: true,
    pointerId: 1,
  });
}

interface UseSidebarDragOptions {
  type: string;
  label: string;
  workspace: Blockly.WorkspaceSvg | null;
  previewDataUrl?: string;
}

export function isOverWorkspace(
  rect: DOMRect,
  clientX: number,
  clientY: number,
): boolean {
  return (
    clientX >= rect.left && clientX <= rect.right && clientY >= rect.top && clientY <= rect.bottom
  );
}

export function useSidebarDrag({ type, label, workspace, previewDataUrl }: UseSidebarDragOptions) {
  const wasDragged = useRef(false);
  const startPos = useRef<{ x: number; y: number } | null>(null);
  const ghostRef = useRef<HTMLDivElement | null>(null);
  const isDragging = useRef(false);

  const blocklyBlockRef = useRef<Blockly.BlockSvg | null>(null);
  const blocklyDragActive = useRef(false);
  const eventGroupRef = useRef<string | null>(null);
  const wsBoundsRef = useRef<DOMRect | null>(null);

  const removeGhost = useCallback(() => {
    if (ghostRef.current) {
      ghostRef.current.remove();
      ghostRef.current = null;
    }
  }, []);

  const createAndPlaceBlock = useCallback(
    (ws: Blockly.WorkspaceSvg, wsCoords: Blockly.utils.Coordinate) => {
      if (SINGLETON_BLOCK_TYPES.has(type) && isSingletonBlockPresent(ws, type)) return null;
      const block = ws.newBlock(type);
      block.initSvg();
      block.render();
      block.moveTo(wsCoords);
      return block;
    },
    [type]
  );

  const abortBlocklyDrag = useCallback((isSuccess = false) => {
    if (blocklyBlockRef.current) {
      if (!isSuccess) {
        if (blocklyDragActive.current) {
          try {
            blocklyBlockRef.current.revertDrag();
          } catch (err) {
            if (import.meta.env.DEV) {
              console.warn("[useSidebarDrag] revertDrag failed:", err);
            }
          }
        }
        try {
          blocklyBlockRef.current.dispose(false);
        } catch (err) {
          if (import.meta.env.DEV) {
            console.warn("[useSidebarDrag] dispose failed:", err);
          }
        }
      }
      blocklyBlockRef.current = null;
      blocklyDragActive.current = false;
    }

    if (eventGroupRef.current) {
      Blockly.Events.setGroup(false);
      eventGroupRef.current = null;
    }
  }, []);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return;
    startPos.current = { x: e.clientX, y: e.clientY };
    wasDragged.current = false;
    isDragging.current = false;
  }, []);

  useEffect(() => {
    let rafId: number | null = null;

    const onMouseMove = (e: MouseEvent) => {
      if (rafId !== null) cancelAnimationFrame(rafId);

      rafId = requestAnimationFrame(() => {
        rafId = null;
        if (!startPos.current) return;

        const dx = e.clientX - startPos.current.x;
        const dy = e.clientY - startPos.current.y;

        if (!isDragging.current && Math.sqrt(dx * dx + dy * dy) > DRAG_THRESHOLD) {
          isDragging.current = true;
          wasDragged.current = true;

          const ghost = document.createElement("div");
          ghost.className = "sidebar-drag-ghost";
          ghost.style.pointerEvents = "none";
          if (previewDataUrl) {
            const img = document.createElement("img");
            img.src = previewDataUrl;
            img.style.maxWidth = "200px";
            img.style.height = "auto";
            img.style.display = "block";
            ghost.appendChild(img);
          } else {
            ghost.classList.add("sidebar-drag-ghost--text");
            ghost.textContent = label;
          }
          document.body.appendChild(ghost);
          ghostRef.current = ghost;
        }

        if (isDragging.current && ghostRef.current) {
          ghostRef.current.style.left = `${e.clientX + 10}px`;
          ghostRef.current.style.top = `${e.clientY - 14}px`;
        }
        if (!isDragging.current || !workspace) return;

        if (!wsBoundsRef.current) {
          wsBoundsRef.current = workspace.getParentSvg().getBoundingClientRect();
        }

        const overWs = isOverWorkspace(wsBoundsRef.current, e.clientX, e.clientY);

        if (overWs && !blocklyBlockRef.current) {
          const wsCoords = Blockly.utils.svgMath.screenToWsCoordinates(
            workspace,
            new Blockly.utils.Coordinate(e.clientX, e.clientY),
          );

          try {
            Blockly.Events.setGroup(true);
            eventGroupRef.current = Blockly.Events.getGroup();

            const block = createAndPlaceBlock(workspace, wsCoords);
            if (!block) {
              abortBlocklyDrag();
              return;
            }

            blocklyBlockRef.current = block;
            // Start drag first to register drag origin correctly, then hide ghost
            block.startDrag(createSyntheticPointerEvent(e));
            blocklyDragActive.current = true;
            if (ghostRef.current) ghostRef.current.style.visibility = "hidden";
          } catch (err) {
            console.error("[useSidebarDrag] Failed to create drag block:", err);
            abortBlocklyDrag();
          }
        } else if (overWs && blocklyBlockRef.current && blocklyDragActive.current) {
          const wsCoords = Blockly.utils.svgMath.screenToWsCoordinates(
            workspace,
            new Blockly.utils.Coordinate(e.clientX, e.clientY),
          );
          blocklyBlockRef.current.drag(wsCoords, createSyntheticPointerEvent(e));
        } else if (!overWs && blocklyBlockRef.current) {
          abortBlocklyDrag(false);
          if (ghostRef.current) ghostRef.current.style.visibility = "visible";
        }
      });
    };

    const onMouseUp = (e: MouseEvent) => {
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }

      if (isDragging.current && workspace) {
        removeGhost();

        if (blocklyBlockRef.current && blocklyDragActive.current) {
          try {
            const pointerEvent = createSyntheticPointerEvent(e);
            blocklyBlockRef.current.endDrag(pointerEvent);
          } catch (err) {
            console.error("[useSidebarDrag] endDrag failure:", err);
            // Fallback: if endDrag fails, ensure block is cleaned if not committed
            if (blocklyBlockRef.current) {
              try { blocklyBlockRef.current.dispose(false); } catch { /* ignore */ }
            }
          } finally {
            // Success flag for abortBlocklyDrag to clear remaining refs
            abortBlocklyDrag(true);
          }
        } else if (!blocklyBlockRef.current) {
          // Re-check bounds on mouseup in case mousemove didn't fire inside
          const currentBounds = workspace.getParentSvg().getBoundingClientRect();
          if (isOverWorkspace(currentBounds, e.clientX, e.clientY)) {
            const wsCoords = Blockly.utils.svgMath.screenToWsCoordinates(
              workspace,
              new Blockly.utils.Coordinate(e.clientX, e.clientY),
            );
            createAndPlaceBlock(workspace, wsCoords);
          }
        }
      }

      const isSuccess = !!(blocklyBlockRef.current && blocklyDragActive.current);
      abortBlocklyDrag(isSuccess);

      startPos.current = null;
      isDragging.current = false;
      removeGhost();
    };

    const handleResize = () => {
      wsBoundsRef.current = null;
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    window.addEventListener("resize", handleResize);

    return () => {
      if (rafId !== null) cancelAnimationFrame(rafId);
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      window.removeEventListener("resize", handleResize);
      abortBlocklyDrag();
      removeGhost();
    };
  }, [type, label, workspace, previewDataUrl, removeGhost, abortBlocklyDrag, createAndPlaceBlock]);

  return { onMouseDown, wasDragged };
}
