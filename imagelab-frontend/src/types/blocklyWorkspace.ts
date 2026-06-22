import * as Blockly from "blockly";

/** Serialized Blockly workspace state (blocks, variables, etc.). */
export type WorkspaceJson = ReturnType<typeof Blockly.serialization.workspaces.save>;
