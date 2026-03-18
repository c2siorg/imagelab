/** Mirrors Blockly.inputTypes.VALUE (= 1). See blockly/core/input_types.ts.
 *  Blockly does not export inputTypes in its ESM build, so the value is
 *  kept here with an explicit reference rather than imported at runtime. */
export const INPUT_TYPE_VALUE = 1;

export type MockField = {
  name?: string;
  getValue: () => unknown;
};

export function field(name: string | undefined, value: unknown): MockField {
  return { name, getValue: () => value };
}

export type MockInput = {
  fieldRow: MockField[];
  type: number;
  // Always present — matches Blockly's real model where connection is never
  // undefined; when nothing is connected, targetBlock() returns null.
  connection: { targetBlock: () => MockBlock | null };
};

export function input(
  fieldRow: MockField[] = [],
  opts?: { type?: number; connected?: MockBlock | null },
): MockInput {
  const type = opts?.type ?? 0;
  const connected = opts?.connected ?? null;
  return {
    fieldRow,
    type,
    // Always supply a connection object; unconnected => targetBlock returns null
    connection: { targetBlock: () => connected },
  };
}

export type MockBlock = {
  type: string;
  inputList: MockInput[];
  getNextBlock: () => MockBlock | null;
};

export function block(
  type: string,
  inputList: MockInput[] = [],
  next: MockBlock | null = null,
): MockBlock {
  return { type, inputList, getNextBlock: () => next };
}

export type MockWorkspace = {
  getTopBlocks: (ordered?: boolean) => MockBlock[];
};

// Minimal interface mirroring only what extractPipeline actually calls.
// MockWorkspace already satisfies this shape — no type cast needed in tests.
export interface ExtractPipelineWorkspace {
  getTopBlocks(ordered?: boolean): MockBlock[];
}

export function workspace(
  topBlocks: MockBlock[],
  opts?: { onGetTopBlocks?: (ordered?: boolean) => void },
): MockWorkspace {
  return {
    getTopBlocks: (ordered?: boolean) => {
      opts?.onGetTopBlocks?.(ordered);
      return topBlocks;
    },
  };
}
