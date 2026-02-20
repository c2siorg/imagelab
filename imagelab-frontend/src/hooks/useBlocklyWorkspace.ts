import { useRef, useEffect, useState, useCallback } from 'react';
import * as Blockly from 'blockly';
import '@blockly/field-angle';
import '@blockly/field-colour';
import '@blockly/field-slider';
import { WorkspaceSearch } from '@blockly/plugin-workspace-search';
import { usePipelineStore } from '../store/pipelineStore';
import { imagelabTheme } from '../blocks/theme';

export function useBlocklyWorkspace() {
  const containerRef = useRef<HTMLDivElement>(null);
  const workspaceRef = useRef<Blockly.WorkspaceSvg | null>(null);
  const [workspace, setWorkspace] = useState<Blockly.WorkspaceSvg | null>(null);
  const setSelectedBlock = usePipelineStore((s) => s.setSelectedBlock);

  const initWorkspace = useCallback(() => {
    if (!containerRef.current || workspaceRef.current) return;

    const ws = Blockly.inject(containerRef.current, {
      readOnly: false,
      move: {
        scrollbars: true,
        drag: true,
        wheel: false,
      },
      trashcan: true,
      renderer: 'zelos',
      theme: imagelabTheme,
      grid: {
        spacing: 20,
        length: 3,
        colour: '#E5E7EB',
        snap: true,
      },
      zoom: {
        controls: true,
        wheel: true,
        startScale: 1.0,
        maxScale: 3,
        minScale: 0.3,
        scaleSpeed: 1.2,
      },
    });

    ws.addChangeListener((event: Blockly.Events.Abstract) => {
      if (event.type === Blockly.Events.SELECTED) {
        const selectedEvent = event as Blockly.Events.Selected;
        if (selectedEvent.newElementId) {
          const block = ws.getBlockById(selectedEvent.newElementId);
          if (block) {
            setSelectedBlock(block.type, block.tooltip as string);
          }
        } else {
          setSelectedBlock(null, null);
        }
      }
    });

    new WorkspaceSearch(ws).init();

    workspaceRef.current = ws;
    setWorkspace(ws);
  }, [setSelectedBlock]);

  useEffect(() => {
    initWorkspace();
    return () => {
      if (workspaceRef.current) {
        workspaceRef.current.dispose();
        workspaceRef.current = null;
        setWorkspace(null);
      }
    };
  }, [initWorkspace]);

  return { containerRef, workspace };
}
