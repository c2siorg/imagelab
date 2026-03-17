import { useRef, useEffect, useState, useCallback } from "react";
import * as Blockly from "blockly";
import "@blockly/field-angle";
import "@blockly/field-colour";
import "@blockly/field-slider";
import { WorkspaceSearch } from "@blockly/plugin-workspace-search";
import { usePipelineStore } from "../store/pipelineStore";
import { imagelabTheme } from "../blocks/theme";
import { SINGLETON_BLOCK_TYPES } from "../utils/blockLimits";
import {
  clearPersistedWorkspace,
  loadPersistedWorkspaceState,
  saveWorkspaceState,
} from "./workspacePersistence";

const SAVE_DEBOUNCE_MS = 500;

const SNAP_RADIUS = 48;
const CONNECTING_SNAP_RADIUS = 68;

// Apply global Blockly configuration once at module load
Blockly.config.snapRadius = SNAP_RADIUS;
Blockly.config.connectingSnapRadius = CONNECTING_SNAP_RADIUS;

const MUTATING_EVENTS = new Set<string>([
  Blockly.Events.BLOCK_CREATE,
  Blockly.Events.BLOCK_DELETE,
  Blockly.Events.BLOCK_CHANGE,
  Blockly.Events.BLOCK_MOVE,
]);

type WorkspaceState = ReturnType<typeof Blockly.serialization.workspaces.save>;

export function useBlocklyWorkspace() {
  const containerRef = useRef<HTMLDivElement>(null);
  const workspaceRef = useRef<Blockly.WorkspaceSvg | null>(null);
  const saveTimeoutRef = useRef<number | null>(null);
  const [workspace, setWorkspace] = useState<Blockly.WorkspaceSvg | null>(null);
  const setSelectedBlock = usePipelineStore((s) => s.setSelectedBlock);
  const updateBlockStats = usePipelineStore((s) => s.updateBlockStats);

  const initWorkspace = useCallback(() => {
    if (!containerRef.current || workspaceRef.current) return;

    Blockly.config.snapRadius = 48;
    Blockly.config.connectingSnapRadius = 68;

    const ws = Blockly.inject(containerRef.current, {
      readOnly: false,
      move: {
        scrollbars: true,
        drag: true,
        wheel: false,
      },
      trashcan: true,
      renderer: "zelos",
      theme: imagelabTheme,
      grid: {
        spacing: 20,
        length: 3,
        colour: "#E5E7EB",
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
    // Load persisted workspace state if available and valid
    const persistedState = loadPersistedWorkspaceState<WorkspaceState>();
    if (persistedState) {
      try {
        Blockly.serialization.workspaces.load(persistedState, ws);
      } catch (err) {
        console.warn("[ImageLab] Failed to restore workspace state; clearing persisted data.", err);
        clearPersistedWorkspace();
        // workspace is already blank — no further action needed
      }
    }

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

      if (event.type === Blockly.Events.BLOCK_CREATE) {
        const createEvent = event as Blockly.Events.BlockCreate;
        const blockId = createEvent.blockId;
        if (!blockId) return;
        const block = ws.getBlockById(blockId);
        if (!block || !SINGLETON_BLOCK_TYPES.has(block.type)) return;
        if (ws.getBlocksByType(block.type).length > 1) {
          block.dispose(false);
        }
      }

      // Update stats when blocks are created, deleted, or changed (which might alter their active state but mainly create/delete impact counts)
      if (
        event.type === Blockly.Events.BLOCK_CREATE ||
        event.type === Blockly.Events.BLOCK_DELETE
      ) {
        updateBlockStats(ws);
      }

      // Debounced save on any change that modifies the workspace (create, delete, change, move)
      if (!event.isUiEvent && MUTATING_EVENTS.has(event.type)) {
        // Clear any existing save timeout to debounce rapid changes
        if (saveTimeoutRef.current !== null) {
          window.clearTimeout(saveTimeoutRef.current);
        }
        saveTimeoutRef.current = window.setTimeout(() => {
          const state = Blockly.serialization.workspaces.save(ws);
          saveWorkspaceState(state);
        }, SAVE_DEBOUNCE_MS);
      }
    });

    new WorkspaceSearch(ws).init();

    workspaceRef.current = ws;
    setWorkspace(ws);
    updateBlockStats(ws); // Initial stats calculation if any blocks loaded
  }, [setSelectedBlock, updateBlockStats]);

  useEffect(() => {
    initWorkspace();
    return () => {
      // Cleanup on unmount: dispose workspace and clear any pending save timeout
      if (saveTimeoutRef.current !== null) {
        window.clearTimeout(saveTimeoutRef.current);
        saveTimeoutRef.current = null;
        // Flush the save synchronously so the last change is not lost
        if (workspaceRef.current) {
          const state = Blockly.serialization.workspaces.save(workspaceRef.current);
          saveWorkspaceState(state);
        }
      }
      if (workspaceRef.current) {
        workspaceRef.current.dispose();
        workspaceRef.current = null;
      }
    };
  }, [initWorkspace]);

  return { containerRef, workspace };
}
