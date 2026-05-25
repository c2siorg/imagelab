import { useCallback, useEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import * as Blockly from "blockly";
import { BookOpen, GripHorizontal, Images, Maximize2, Minimize2 } from "lucide-react";
import InfoPane from "./InfoPane";
import StepResultsPane from "./StepResultsPane";

interface BottomPanelProps {
  workspace: Blockly.WorkspaceSvg | null;
}

type BottomTab = "steps" | "analysis";

const MIN_PANEL_HEIGHT = 120;
const DEFAULT_PANEL_HEIGHT = 160;
const EXPANDED_PANEL_HEIGHT = 360;
const STORAGE_KEY = "imagelab.bottomPanelHeight";

function getMaxPanelHeight() {
  if (typeof window === "undefined") return EXPANDED_PANEL_HEIGHT;
  return Math.max(MIN_PANEL_HEIGHT, Math.floor(window.innerHeight * 0.55));
}

function clampPanelHeight(height: number) {
  return Math.min(Math.max(height, MIN_PANEL_HEIGHT), getMaxPanelHeight());
}

function getInitialPanelHeight() {
  if (typeof window === "undefined") return DEFAULT_PANEL_HEIGHT;
  const savedHeight = Number(window.localStorage.getItem(STORAGE_KEY));
  return Number.isFinite(savedHeight) && savedHeight > 0
    ? clampPanelHeight(savedHeight)
    : DEFAULT_PANEL_HEIGHT;
}

export default function BottomPanel({ workspace }: BottomPanelProps) {
  const [activeTab, setActiveTab] = useState<BottomTab>("steps");
  const [height, setHeight] = useState(getInitialPanelHeight);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ y: 0, height: 0 });

  const resizeWorkspace = useCallback(() => {
    if (!workspace) return;
    requestAnimationFrame(() => Blockly.svgResize(workspace));
  }, [workspace]);

  const updateHeight = useCallback(
    (nextHeight: number) => {
      const clampedHeight = clampPanelHeight(nextHeight);
      setHeight(clampedHeight);
      window.localStorage.setItem(STORAGE_KEY, String(clampedHeight));
      resizeWorkspace();
    },
    [resizeWorkspace],
  );

  useEffect(() => {
    if (!isDragging) return;

    const handlePointerMove = (event: PointerEvent) => {
      const deltaY = dragStartRef.current.y - event.clientY;
      updateHeight(dragStartRef.current.height + deltaY);
    };

    const handlePointerUp = () => {
      setIsDragging(false);
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
    };
  }, [isDragging, updateHeight]);

  useEffect(() => {
    resizeWorkspace();
  }, [height, resizeWorkspace]);

  const handleResizeStart = (event: ReactPointerEvent<HTMLButtonElement>) => {
    event.preventDefault();
    dragStartRef.current = { y: event.clientY, height };
    setIsDragging(true);
    document.body.style.userSelect = "none";
    document.body.style.cursor = "row-resize";
  };

  const expandedHeight = clampPanelHeight(EXPANDED_PANEL_HEIGHT);
  const isExpanded = height >= expandedHeight - 8;

  const toggleExpanded = () => {
    updateHeight(isExpanded ? DEFAULT_PANEL_HEIGHT : expandedHeight);
  };

  const tabClass = (tab: BottomTab) =>
    `h-8 px-4 flex items-center gap-1.5 border-r border-gray-200 dark:border-gray-700 text-xs font-medium transition-colors ${
      activeTab === tab
        ? "bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        : "bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700"
    }`;

  return (
    <div
      className="relative flex flex-col border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex-shrink-0"
      style={{ height }}
    >
      <button
        type="button"
        onPointerDown={handleResizeStart}
        className="absolute -top-2 left-0 right-0 h-4 cursor-row-resize flex items-center justify-center text-gray-300 dark:text-gray-600 hover:text-indigo-500 dark:hover:text-indigo-400 z-10"
        title="Resize bottom panel"
        aria-label="Resize bottom panel"
      >
        <GripHorizontal size={16} />
      </button>
      <div className="h-8 flex items-center border-b border-gray-200 dark:border-gray-700">
        <div className="flex min-w-0 flex-1">
          <button className={tabClass("steps")} onClick={() => setActiveTab("steps")}>
            <Images size={14} />
            Step results
          </button>
          <button className={tabClass("analysis")} onClick={() => setActiveTab("analysis")}>
            <BookOpen size={14} />
            Image analysis panel
          </button>
        </div>
        <button
          type="button"
          onClick={toggleExpanded}
          className="h-8 w-8 flex items-center justify-center text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-800 dark:hover:text-gray-100 transition-colors"
          title={isExpanded ? "Collapse bottom panel" : "Expand bottom panel"}
          aria-label={isExpanded ? "Collapse bottom panel" : "Expand bottom panel"}
        >
          {isExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
        </button>
      </div>
      <div className="flex-1 min-h-0">
        {activeTab === "steps" ? <StepResultsPane workspace={workspace} /> : <InfoPane />}
      </div>
    </div>
  );
}
