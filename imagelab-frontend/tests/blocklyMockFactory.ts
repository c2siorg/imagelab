export const INPUT_TYPE_VALUE = 1;

export type MockField = {
  name?: string;
  getValue: () => unknown;
};

export function field(name: string, value: unknown): MockField {
  return { name, getValue: () => value };
}

export type MockInput = {
  fieldRow: MockField[];
  type: number;
  connection?: { targetBlock: () => MockBlock | null };
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
    connection: connected ? { targetBlock: () => connected } : undefined,
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

export function workspace(topBlocks: MockBlock[]): MockWorkspace {
  return { getTopBlocks: () => topBlocks };
}
