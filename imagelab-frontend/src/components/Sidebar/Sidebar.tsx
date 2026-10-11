import { useState, useEffect, useMemo, useCallback } from "react";
import * as Blockly from "blockly";
import { categories } from "../../blocks/categories";
import { useBlockPreviews } from "../../hooks/useBlockPreviews";
import { SINGLETON_BLOCK_TYPES } from "../../utils/blockLimits";
import { useMacroStore } from "../../store/useMacroStore";
import { refreshMacroBlockInstances, registerMacroBlock } from "../../blocks/macroBlock";
import CategorySection from "./CategorySection";
import { Search, X, AlertCircle, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import type { CategoryInfo } from "../../blocks/categories";
import type { MacroDefinition } from "../../types/macro";
import EditMacroModal from "../modals/EditMacroModal";
import {
  loadSidebarCollapsedState,
  saveSidebarCollapsedState,
} from "../../hooks/workspacePersistence";

interface SidebarProps {
  workspace: Blockly.WorkspaceSvg | null;
  defaultCollapsed?: boolean;
}

export default function Sidebar({ workspace, defaultCollapsed }: SidebarProps) {
  const previews = useBlockPreviews();
  const [tick, setTick] = useState(0);
  const [query, setQuery] = useState("");
  const [editingMacro, setEditingMacro] = useState<MacroDefinition | null>(null);
  const [isCollapsed, setIsCollapsed] = useState(() => {
    return defaultCollapsed !== undefined ? defaultCollapsed : loadSidebarCollapsedState();
  });

  useEffect(() => {
    if (defaultCollapsed !== undefined) {
      setIsCollapsed(defaultCollapsed);
    }
  }, [defaultCollapsed]);

  const toggleCollapse = useCallback(() => {
    setIsCollapsed((prev) => {
      const next = !prev;
      saveSidebarCollapsedState(next);
      return next;
    });
  }, []);

  useEffect(() => {
    if (!workspace) return;
    Blockly.svgResize(workspace);
    const rafId = requestAnimationFrame(() => {
      Blockly.svgResize(workspace);
    });
    const timerId = window.setTimeout(() => {
      Blockly.svgResize(workspace);
    }, 220);
    return () => {
      cancelAnimationFrame(rafId);
      window.clearTimeout(timerId);
    };
  }, [isCollapsed, workspace]);

  // ── Macro store subscription ──────────────────────────────────────────────
  const macros = useMacroStore((state) => state.macros);
  const loadMacros = useMacroStore((state) => state.loadMacros);
  const removeMacro = useMacroStore((state) => state.removeMacro);
  const deletionError = useMacroStore((state) => state.deletionError);
  const clearDeletionError = useMacroStore((state) => state.clearDeletionError);

  useEffect(() => {
    void loadMacros();
  }, [loadMacros]);

  useEffect(() => {
    // Refresh existing macro block instances and register any new macro blocks
    for (const macro of macros) {
      registerMacroBlock(macro);
      refreshMacroBlockInstances(workspace, macro);
    }
  }, [macros, workspace]);

  const editMacro = (macroId: string) => {
    const macro = macros.find((candidate) => candidate.id === macroId);
    if (macro) setEditingMacro(macro);
  };

  const deleteMacro = (macroId: string) => {
    clearDeletionError();
    void removeMacro(macroId).catch(() => {
      // Error is handled by the store and displayed via deletionError state
    });
  };

  // Build the dynamic Macros category. Register each block type before render.
  const macrosCategory = useMemo((): CategoryInfo | null => {
    if (macros.length === 0) return null;
    const blocks = macros.map((macro) => {
      registerMacroBlock(macro);
      return { type: `macro_${macro.id}`, label: macro.name };
    });
    return {
      name: "Macros",
      icon: "Package",
      colour: "#7058a3",
      blocks,
    };
  }, [macros]);

  // ── Workspace block-count tracking for singleton enforcement ──────────────
  useEffect(() => {
    if (!workspace) return;
    const listener = (event: Blockly.Events.Abstract) => {
      if (
        event.type === Blockly.Events.BLOCK_CREATE ||
        event.type === Blockly.Events.BLOCK_DELETE
      ) {
        setTick((t) => t + 1);
      }
    };
    workspace.addChangeListener(listener);
    return () => workspace.removeChangeListener(listener);
  }, [workspace]);

  const presentSingletons = useMemo(() => {
    if (!workspace) return new Set<string>();
    const present = new Set<string>();
    for (const type of SINGLETON_BLOCK_TYPES) {
      if (workspace.getBlocksByType(type).length > 0) {
        present.add(type);
      }
    }
    return present;
    // eslint-disable-next-line react-hooks/exhaustive-deps -- tick triggers recomputation on block create/delete
  }, [workspace, tick]);

  return (
    <aside
      aria-label="Blocks sidebar"
      className={`h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex-shrink-0 flex flex-col transition-all duration-200 ease-in-out relative ${
        isCollapsed ? "w-12" : "w-80"
      }`}
      onTransitionEnd={() => {
        if (workspace) {
          Blockly.svgResize(workspace);
        }
      }}
    >
      {/* Collapsed Rail View */}
      {isCollapsed && (
        <div className="flex flex-col items-center py-2 px-1 flex-1">
          <button
            type="button"
            onClick={toggleCollapse}
            aria-label="Expand Blocks sidebar"
            aria-expanded={false}
            aria-controls="sidebar-blocks-content"
            title="Expand Blocks sidebar"
            className="p-1.5 rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-800 dark:hover:text-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-400"
          >
            <PanelLeftOpen size={18} aria-hidden="true" />
          </button>
          <span
            className="mt-4 text-[11px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 select-none"
            style={{ writingMode: "vertical-rl", transform: "rotate(180deg)" }}
          >
            Blocks
          </span>
        </div>
      )}

      {/* Expanded Content View (keeps category & search state mounted across collapse/expand) */}
      <div
        id="sidebar-blocks-content"
        className={`flex-1 flex flex-col min-h-0 overflow-hidden ${isCollapsed ? "hidden" : ""}`}
        aria-hidden={isCollapsed}
      >
        <div className="flex-shrink-0 px-3 py-2 border-b border-gray-200 dark:border-gray-700 flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Blocks
            </h2>
            <button
              type="button"
              onClick={toggleCollapse}
              aria-label="Collapse Blocks sidebar"
              aria-expanded={true}
              aria-controls="sidebar-blocks-content"
              title="Collapse Blocks sidebar"
              className="p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              <PanelLeftClose size={16} aria-hidden="true" />
            </button>
          </div>
          <div className="relative">
            <Search
              size={12}
              className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
            />
            <input
              type="text"
              aria-label="Search blocks"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search blocks..."
              className="w-full pl-7 pr-7 py-1.5 text-xs border border-gray-200 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-indigo-400 focus:border-indigo-400 placeholder-gray-400"
            />
            {query && (
              <button
                type="button"
                title="Clear search"
                aria-label="Clear search"
                onClick={() => setQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 cursor-pointer text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <X size={12} aria-hidden="true" />
              </button>
            )}
          </div>
        </div>
        <div className="overflow-y-auto flex-1">
          {categories.map((category) => (
            <CategorySection
              key={`${category.name}-${category.icon}`}
              category={category}
              workspace={workspace}
              previews={previews}
              disabledTypes={presentSingletons}
              defaultOpen={category.name === "Basic"}
              searchQuery={query}
            />
          ))}

          {/* Dynamic Macros category — rendered only when saved macros exist */}
          {macrosCategory && (
            <CategorySection
              key="macros-category"
              category={macrosCategory}
              workspace={workspace}
              previews={previews}
              disabledTypes={presentSingletons}
              defaultOpen={false}
              searchQuery={query}
              onEditMacro={editMacro}
              onDeleteMacro={deleteMacro}
            />
          )}
        </div>
      </div>
      {editingMacro && (
        <EditMacroModal macro={editingMacro} onClose={() => setEditingMacro(null)} />
      )}
      {deletionError && (
        <div className="fixed bottom-4 right-4 max-w-md bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 rounded-lg p-4 shadow-lg z-50">
          <div className="flex items-start gap-3">
            <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium mb-1">Cannot Delete Macro</p>
              <p className="text-xs">{deletionError}</p>
            </div>
            <button
              onClick={clearDeletionError}
              className="text-red-400 hover:text-red-600 dark:hover:text-red-300"
              aria-label="Close error"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
