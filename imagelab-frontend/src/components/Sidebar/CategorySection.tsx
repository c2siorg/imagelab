import { useState, useMemo } from "react";
import * as Blockly from "blockly";
import {
  ChevronRight,
  ChevronDown,
  Image,
  Move,
  Palette,
  Pencil,
  Droplets,
  Filter,
  SlidersHorizontal,
  Scan,
  Shuffle,
  Zap,
  Layers,
} from "lucide-react";
import type { CategoryInfo } from "../../blocks/categories";
import type { BlockPreview } from "../../hooks/useBlockPreviews";
import BlockItem from "./BlockItem";

const iconMap: Record<string, React.ComponentType<{ size?: number; color?: string }>> = {
  Image,
  Move,
  Palette,
  Pencil,
  Droplets,
  Filter,
  SlidersHorizontal,
  Scan,
  Shuffle,
  Zap,
  Layers,
};

interface CategorySectionProps {
  category: CategoryInfo;
  workspace: Blockly.WorkspaceSvg | null;
  previews: Map<string, BlockPreview>;
  disabledTypes: Set<string>;
  defaultOpen?: boolean;
  searchQuery?: string;
}

export default function CategorySection({
  category,
  workspace,
  previews,
  disabledTypes,
  defaultOpen,
  searchQuery = "",
}: CategorySectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen ?? false);
  const Icon = iconMap[category.icon];

  const isSearching = searchQuery.trim().length > 0;

  const filteredBlocks = useMemo(() => {
    if (!isSearching) return category.blocks;
    const lowerQuery = searchQuery.toLowerCase();
    return category.blocks.filter((b) => b.label.toLowerCase().includes(lowerQuery));
  }, [isSearching, searchQuery, category.blocks]);

  const effectiveOpen = isSearching ? filteredBlocks.length > 0 : isOpen;

  if (isSearching && filteredBlocks.length === 0) return null;

  return (
    <div className="border-b border-gray-200">
      <button
        type="button"
        onClick={() => {
          if (!isSearching) setIsOpen((prev) => !prev);
        }}
        aria-expanded={effectiveOpen}
        className={`w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-50 transition-colors ${isSearching ? "cursor-default" : ""}`}
      >
        {effectiveOpen ? (
          <ChevronDown size={14} className={isSearching ? "text-gray-200" : "text-gray-400"} />
        ) : (
          <ChevronRight size={14} className={isSearching ? "text-gray-200" : "text-gray-400"} />
        )}
        {Icon && <Icon size={16} color={category.colour} />}
        <span className="text-sm font-medium text-gray-700">{category.name}</span>
        <span className="ml-auto text-xs text-gray-400 font-normal">
          {isSearching
            ? `${filteredBlocks.length}/${category.blocks.length}`
            : category.blocks.length}
        </span>
      </button>
      {effectiveOpen && (
        <div className="pb-1 pl-2">
          {filteredBlocks.map((block) => (
            <BlockItem
              key={block.type}
              type={block.type}
              label={block.label}
              workspace={workspace}
              preview={previews.get(block.type)}
              disabled={disabledTypes.has(block.type)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
