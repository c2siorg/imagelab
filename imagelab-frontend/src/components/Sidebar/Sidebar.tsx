import { useState, useEffect, useMemo } from "react";
import * as Blockly from "blockly";
import { categories } from "../../blocks/categories";
import { useBlockPreviews } from "../../hooks/useBlockPreviews";
import { SINGLETON_BLOCK_TYPES } from "../../utils/blockLimits";
import CategorySection from "./CategorySection";
import { Search, X } from "lucide-react";

interface SidebarProps {
  workspace: Blockly.WorkspaceSvg | null;
}

export default function Sidebar({ workspace }: SidebarProps) {
  const previews = useBlockPreviews();
  const [tick, setTick] = useState(0);
  const [query, setQuery] = useState("");

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
    <div className="w-80 h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex-shrink-0 flex flex-col">
      <div className="flex-shrink-0 px-3 py-2 border-b border-gray-200 dark:border-gray-700 flex flex-col gap-2">
        <h2 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          Blocks
        </h2>
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
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              <X size={12} aria-hidden="true" />
            </button>
          )}
        </div>
      </div>
      <div className="overflow-y-auto flex-1">
        {categories.map((category) => (
          <CategorySection
            key={category.name}
            category={category}
            workspace={workspace}
            previews={previews}
            disabledTypes={presentSingletons}
            defaultOpen={category.name === "Basic"}
            searchQuery={query}
          />
        ))}
      </div>
    </div>
  );
}
