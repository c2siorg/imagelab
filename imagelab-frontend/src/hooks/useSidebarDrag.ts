import { useRef, useCallback, useEffect } from 'react';
import * as Blockly from 'blockly';

const DRAG_THRESHOLD = 5;

interface UseSidebarDragOptions {
  type: string;
  label: string;
  workspace: Blockly.WorkspaceSvg | null;
  previewDataUrl?: string;
}

export function useSidebarDrag({ type, label, workspace, previewDataUrl }: UseSidebarDragOptions) {
  const wasDragged = useRef(false);
  const startPos = useRef<{ x: number; y: number } | null>(null);
  const ghostRef = useRef<HTMLDivElement | null>(null);
  const isDragging = useRef(false);

  const removeGhost = useCallback(() => {
    if (ghostRef.current) {
      ghostRef.current.remove();
      ghostRef.current = null;
    }
  }, []);

  const onMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return;
      startPos.current = { x: e.clientX, y: e.clientY };
      wasDragged.current = false;
      isDragging.current = false;
    },
    []
  );

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!startPos.current) return;

      const dx = e.clientX - startPos.current.x;
      const dy = e.clientY - startPos.current.y;

      if (!isDragging.current && Math.sqrt(dx * dx + dy * dy) > DRAG_THRESHOLD) {
        isDragging.current = true;
        wasDragged.current = true;

        const ghost = document.createElement('div');
        ghost.className = 'sidebar-drag-ghost';
        if (previewDataUrl) {
          const img = document.createElement('img');
          img.src = previewDataUrl;
          img.style.maxWidth = '200px';
          img.style.height = 'auto';
          img.style.display = 'block';
          ghost.appendChild(img);
        } else {
          ghost.classList.add('sidebar-drag-ghost--text');
          ghost.textContent = label;
        }
        document.body.appendChild(ghost);
        ghostRef.current = ghost;
      }

      if (isDragging.current && ghostRef.current) {
        ghostRef.current.style.left = `${e.clientX + 10}px`;
        ghostRef.current.style.top = `${e.clientY - 14}px`;
      }
    };

    const onMouseUp = (e: MouseEvent) => {
      if (isDragging.current && workspace) {
        removeGhost();

        const svgElement = workspace.getParentSvg();
        const rect = svgElement.getBoundingClientRect();

        if (
          e.clientX >= rect.left &&
          e.clientX <= rect.right &&
          e.clientY >= rect.top &&
          e.clientY <= rect.bottom
        ) {
          const wsCoords = Blockly.utils.svgMath.screenToWsCoordinates(
            workspace,
            new Blockly.utils.Coordinate(e.clientX, e.clientY)
          );
          const block = workspace.newBlock(type);
          block.initSvg();
          block.render();
          block.moveTo(wsCoords);
        }
      }

      startPos.current = null;
      isDragging.current = false;
      removeGhost();
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);

    return () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      removeGhost();
    };
  }, [type, label, workspace, previewDataUrl, removeGhost]);

  return { onMouseDown, wasDragged };
}
