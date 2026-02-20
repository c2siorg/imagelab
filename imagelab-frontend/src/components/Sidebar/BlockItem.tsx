import * as Blockly from 'blockly';
import { useSidebarDrag } from '../../hooks/useSidebarDrag';

interface BlockItemProps {
  type: string;
  label: string;
  workspace: Blockly.WorkspaceSvg | null;
  preview?: { svgDataUrl: string; svgMarkup: string; width: number; height: number } | null;
}

export default function BlockItem({ type, label, workspace, preview }: BlockItemProps) {
  const { onMouseDown, wasDragged } = useSidebarDrag({
    type,
    label,
    workspace,
    previewDataUrl: preview?.svgDataUrl,
  });

  const handleClick = () => {
    if (wasDragged.current) return;
    if (!workspace) return;
    Blockly.serialization.blocks.append({ type, id: undefined }, workspace);
  };

  return (
    <button
      onClick={handleClick}
      onMouseDown={onMouseDown}
      title={label}
      className="w-full py-1 px-1 hover:bg-gray-50 rounded transition-colors cursor-grab active:cursor-grabbing"
    >
      {preview ? (
        <div
          className="block-preview-inline"
          // SVG is generated internally by our Blockly workspace, not user input
          dangerouslySetInnerHTML={{ __html: preview.svgMarkup }}
        />
      ) : (
        <span className="text-xs text-gray-400 italic pl-1">{label}</span>
      )}
    </button>
  );
}
