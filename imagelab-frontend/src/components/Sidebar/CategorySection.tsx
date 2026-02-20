import { useState } from 'react';
import * as Blockly from 'blockly';
import { ChevronRight, ChevronDown, Image, Move, Palette, Pencil, Droplets, Filter, SlidersHorizontal, Scan, Shuffle } from 'lucide-react';
import type { CategoryInfo } from '../../blocks/categories';
import type { BlockPreview } from '../../hooks/useBlockPreviews';
import BlockItem from './BlockItem';

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
};

interface CategorySectionProps {
  category: CategoryInfo;
  workspace: Blockly.WorkspaceSvg | null;
  previews: Map<string, BlockPreview>;
}

export default function CategorySection({ category, workspace, previews }: CategorySectionProps) {
  const [isOpen, setIsOpen] = useState(false);
  const Icon = iconMap[category.icon];

  return (
    <div className="border-b border-gray-200">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-50 transition-colors"
      >
        {isOpen ? <ChevronDown size={14} className="text-gray-400" /> : <ChevronRight size={14} className="text-gray-400" />}
        {Icon && <Icon size={16} color={category.colour} />}
        <span className="text-sm font-medium text-gray-700">{category.name}</span>
        <span className="ml-auto text-xs text-gray-400 font-normal">{category.blocks.length}</span>
      </button>
      {isOpen && (
        <div className="pb-1 pl-2">
          {category.blocks.map((block) => (
            <BlockItem key={block.type} type={block.type} label={block.label} workspace={workspace} preview={previews.get(block.type)} />
          ))}
        </div>
      )}
    </div>
  );
}
