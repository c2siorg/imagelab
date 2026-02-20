import * as Blockly from 'blockly';
import { categories } from '../../blocks/categories';
import { useBlockPreviews } from '../../hooks/useBlockPreviews';
import CategorySection from './CategorySection';

interface SidebarProps {
  workspace: Blockly.WorkspaceSvg | null;
}

export default function Sidebar({ workspace }: SidebarProps) {
  const previews = useBlockPreviews();

  return (
    <div className="w-80 h-full bg-white border-r border-gray-200 overflow-y-auto flex-shrink-0">
      <div className="px-3 py-2 border-b border-gray-200">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Blocks</h2>
      </div>
      {categories.map((category) => (
        <CategorySection key={category.name} category={category} workspace={workspace} previews={previews} />
      ))}
    </div>
  );
}
