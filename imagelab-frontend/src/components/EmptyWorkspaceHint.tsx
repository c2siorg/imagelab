import { useCallback, useSyncExternalStore } from "react";
import * as Blockly from "blockly";

interface EmptyWorkspaceHintProps {
  workspace: Blockly.WorkspaceSvg | null;
}

function hasBlocks(workspace: Blockly.WorkspaceSvg | null): boolean {
  return workspace !== null && workspace.getTopBlocks(false).length > 0;
}

/** Centred hint over the Blockly canvas, shown only while the workspace has no blocks. */
export default function EmptyWorkspaceHint({ workspace }: EmptyWorkspaceHintProps) {
  const subscribe = useCallback(
    (onChange: () => void) => {
      if (!workspace) return () => {};
      const listener = (event: Blockly.Events.Abstract) => {
        if (
          event.type === Blockly.Events.BLOCK_CREATE ||
          event.type === Blockly.Events.BLOCK_DELETE
        ) {
          onChange();
        }
      };
      workspace.addChangeListener(listener);
      return () => workspace.removeChangeListener(listener);
    },
    [workspace],
  );
  const isEmpty = useSyncExternalStore(subscribe, () => !hasBlocks(workspace));

  if (!workspace || !isEmpty) return null;

  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div className="text-center">
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
          Drag a block from the Blocks panel to begin
        </p>
        <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">
          Start with Read Image under Basic to load an image
        </p>
      </div>
    </div>
  );
}
