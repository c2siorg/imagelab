/**
 * @vitest-environment jsdom
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, render, screen } from "@testing-library/react";
import * as Blockly from "blockly";
import EmptyWorkspaceHint from "../../src/components/EmptyWorkspaceHint";

const HINT_TEXT = "Drag a block from the Blocks panel to begin";

type Listener = (event: Blockly.Events.Abstract) => void;

function fakeWorkspace(initialBlockCount: number) {
  let blockCount = initialBlockCount;
  const listeners = new Set<Listener>();
  const workspace = {
    getTopBlocks: vi.fn(() => Array.from({ length: blockCount })),
    addChangeListener: vi.fn((listener: Listener) => {
      listeners.add(listener);
      return listener;
    }),
    removeChangeListener: vi.fn((listener: Listener) => {
      listeners.delete(listener);
    }),
  };
  const fire = (type: string, nextBlockCount: number) => {
    blockCount = nextBlockCount;
    for (const listener of listeners) {
      listener({ type } as Blockly.Events.Abstract);
    }
  };
  return { workspace: workspace as unknown as Blockly.WorkspaceSvg, fire, listeners };
}

describe("EmptyWorkspaceHint", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders nothing until the workspace exists", () => {
    render(<EmptyWorkspaceHint workspace={null} />);

    expect(screen.queryByText(HINT_TEXT)).toBeNull();
  });

  it("shows the hint when the workspace has no blocks", () => {
    const { workspace } = fakeWorkspace(0);

    render(<EmptyWorkspaceHint workspace={workspace} />);

    expect(screen.getByText(HINT_TEXT)).toBeTruthy();
  });

  it("does not show the hint when blocks were restored into the workspace", () => {
    const { workspace } = fakeWorkspace(2);

    render(<EmptyWorkspaceHint workspace={workspace} />);

    expect(screen.queryByText(HINT_TEXT)).toBeNull();
  });

  it("hides on block create and reappears once the last block is deleted", () => {
    const { workspace, fire } = fakeWorkspace(0);

    render(<EmptyWorkspaceHint workspace={workspace} />);
    expect(screen.getByText(HINT_TEXT)).toBeTruthy();

    act(() => fire(Blockly.Events.BLOCK_CREATE, 1));
    expect(screen.queryByText(HINT_TEXT)).toBeNull();

    act(() => fire(Blockly.Events.BLOCK_DELETE, 0));
    expect(screen.getByText(HINT_TEXT)).toBeTruthy();
  });

  it("ignores events that do not add or remove blocks", () => {
    const { workspace, fire } = fakeWorkspace(0);

    render(<EmptyWorkspaceHint workspace={workspace} />);

    act(() => fire(Blockly.Events.SELECTED, 0));
    expect(screen.getByText(HINT_TEXT)).toBeTruthy();
  });

  it("removes its change listener on unmount", () => {
    const { workspace, listeners } = fakeWorkspace(0);

    const { unmount } = render(<EmptyWorkspaceHint workspace={workspace} />);
    expect(listeners.size).toBe(1);

    unmount();
    expect(listeners.size).toBe(0);
  });
});
