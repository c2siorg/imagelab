import * as Blockly from "blockly";
import type { WorkspaceJson } from "../types/blocklyWorkspace";

const READ_IMAGE_BLOCK_TYPE = "basic_readimage";
const FILENAME_LABEL_FIELD = "filename_label";

export function loadWorkspaceState(workspace: Blockly.WorkspaceSvg, state: WorkspaceJson): void {
  const snapshot = Blockly.serialization.workspaces.save(workspace);
  workspace.clear();

  try {
    Blockly.serialization.workspaces.load(state, workspace);
  } catch (loadErr) {
    Blockly.serialization.workspaces.load(snapshot, workspace);
    throw loadErr;
  }

  workspace.getBlocksByType(READ_IMAGE_BLOCK_TYPE, false).forEach((block) => {
    block.getField(FILENAME_LABEL_FIELD)?.setValue("No image");
  });
}
