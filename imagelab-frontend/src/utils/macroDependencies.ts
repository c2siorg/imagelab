import { useMacroStore } from "../store/useMacroStore";
import type { MacroDefinition } from "../types/macro";

/**
 * Finds saved macros that bind one of a target macro's serialized exposed
 * field keys (for example, `blur_1__kernelSize`).
 */
export function findDependentMacros(
  targetMacroId: string,
  unexposedParamNames: string[],
): MacroDefinition[] {
  const removedKeys = new Set(unexposedParamNames);
  if (removedKeys.size === 0) return [];

  return useMacroStore.getState().macros.filter(
    (macro) =>
      macro.id !== targetMacroId &&
      macro.graph.nodes.some((node) => {
        if ((node.type ?? node.op) !== `macro_${targetMacroId}`) return false;
        return Object.keys(node.params ?? {}).some((fieldKey) => removedKeys.has(fieldKey));
      }),
  );
}
