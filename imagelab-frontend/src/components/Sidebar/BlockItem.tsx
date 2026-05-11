import * as Blockly from "blockly";
import { useSidebarDrag } from "../../hooks/useSidebarDrag";
import { SINGLETON_BLOCK_TYPES, isSingletonBlockPresent } from "../../utils/blockLimits";

interface BlockItemProps {
  type: string;
  label: string;
  workspace: Blockly.WorkspaceSvg | null;
  preview?: { svgDataUrl: string; svgMarkup: string; width: number; height: number } | null;
  disabled?: boolean;
}

export default function BlockItem({ type, label, workspace, preview, disabled }: BlockItemProps) {
  const { onMouseDown, wasDragged } = useSidebarDrag({
    type,
    label,
    workspace,
    previewDataUrl: preview?.svgDataUrl,
  });

  const handleClick = () => {
    if (wasDragged.current) return;
    if (!workspace) return;
    if (SINGLETON_BLOCK_TYPES.has(type) && isSingletonBlockPresent(workspace, type)) return;
    Blockly.serialization.blocks.append({ type, id: undefined }, workspace);
  };

  const tooltipText = disabled ? `Only one ${label} block allowed` : label;

  return (
    <button
      onClick={disabled ? undefined : handleClick}
      onMouseDown={disabled ? undefined : onMouseDown}
      title={tooltipText}
      className={`w-full py-1 px-1 rounded transition-colors ${
        disabled
          ? "opacity-40 cursor-not-allowed"
          : "hover:bg-gray-50 dark:hover:bg-gray-700 cursor-grab active:cursor-grabbing"
      }`}
    >
      {preview ? (
        <div
          className="block-preview-inline"
          // SVG is generated internally by our Blockly workspace, not user input
          dangerouslySetInnerHTML={{ __html: preview.svgMarkup }}
        />
      ) : (
        <span className="text-xs text-gray-400 dark:text-gray-500 italic pl-1">{label}</span>
      )}
    </button>
  );
}
