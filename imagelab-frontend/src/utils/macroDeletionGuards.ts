import * as Blockly from "blockly";
import type { MacroDefinition } from "../types/macro";

/**
 * Checks if a macro is currently placed on the active Blockly workspace.
 * @param workspace - The Blockly workspace to check
 * @param macroId - The ID of the macro to check for
 * @returns true if the macro is placed on the workspace, false otherwise
 */
export function isMacroInWorkspace(
  workspace: Blockly.WorkspaceSvg | null,
  macroId: string,
): boolean {
  if (!workspace) return false;
  const blocks = workspace.getBlocksByType(`macro_${macroId}`, false);
  return blocks.length > 0;
}

/**
 * Finds macros that depend on a target macro (i.e., the target macro is used inside their graphs).
 * @param targetMacroId - The ID of the macro to check for dependents
 * @param allMacros - All available macro definitions
 * @returns Array of macro definitions that depend on the target macro
 */
export function getMacroDependents(
  targetMacroId: string,
  allMacros: MacroDefinition[],
): MacroDefinition[] {
  return allMacros.filter((macro) => {
    if (macro.id === targetMacroId) return false;
    return macro.graph.nodes.some((node) => (node.type ?? node.op) === `macro_${targetMacroId}`);
  });
}

/**
 * Result type for safe deletion checks.
 */
export interface DeletionGuardResult {
  canDelete: boolean;
  error?: string;
  dependentMacros?: MacroDefinition[];
}

/**
 * Performs comprehensive deletion guard checks before allowing macro deletion.
 * Checks both workspace usage and nested macro dependencies.
 * @param workspace - The Blockly workspace to check for macro instances
 * @param macroId - The ID of the macro to delete
 * @param allMacros - All available macro definitions
 * @returns DeletionGuardResult indicating if deletion is safe or why it's blocked
 */
export function safeDeleteMacro(
  workspace: Blockly.WorkspaceSvg | null,
  macroId: string,
  allMacros: MacroDefinition[],
): DeletionGuardResult {
  // Guard 1: Workspace check - macro is currently placed on canvas
  if (isMacroInWorkspace(workspace, macroId)) {
    return {
      canDelete: false,
      error: `Cannot delete macro: it is currently placed on the workspace. Remove all instances of this macro from the canvas first.`,
    };
  }

  // Guard 2: Nested dependency check - macro is used inside other saved macros
  const dependents = getMacroDependents(macroId, allMacros);
  if (dependents.length > 0) {
    const dependentNames = dependents.map((m) => m.name).join(", ");
    return {
      canDelete: false,
      error: `Cannot delete macro: it is used inside other macros (${dependentNames}). Remove this macro from those parent macros first.`,
      dependentMacros: dependents,
    };
  }

  return { canDelete: true };
}
