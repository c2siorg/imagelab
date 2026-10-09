/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";
import * as Blockly from "blockly";
import { useBlocklyWorkspace } from "../../src/hooks/useBlocklyWorkspace";
import { usePipelineStore } from "../../src/store/pipelineStore";
import type { StepResult } from "../../src/store/pipelineStore";

// Blockly.inject needs real SVG layout, which jsdom does not provide. Replace it
// with a fake workspace so the hook's own change listener can be driven directly.
vi.mock("blockly", async (importOriginal) => {
  const actual = await importOriginal<typeof import("blockly")>();
  return {
    ...actual,
    inject: vi.fn(),
    svgResize: vi.fn(),
    serialization: {
      ...actual.serialization,
      workspaces: { ...actual.serialization.workspaces, save: vi.fn(() => ({})), load: vi.fn() },
    },
  };
});

vi.mock("@blockly/plugin-workspace-search", () => ({
  WorkspaceSearch: class {
    init() {}
  },
}));

type FakeBlock = { id: string; type: string; dispose: ReturnType<typeof vi.fn> };
type ChangeListener = (event: Blockly.Events.Abstract) => void;

function fakeBlock(id: string, type: string): FakeBlock {
  return { id, type, dispose: vi.fn() };
}

function createFakeWorkspace() {
  const blocks: FakeBlock[] = [];
  let listener: ChangeListener | null = null;
  const ws = {
    addChangeListener: vi.fn((fn: ChangeListener) => {
      listener = fn;
      return fn;
    }),
    getBlockById: vi.fn((id: string) => blocks.find((b) => b.id === id) ?? null),
    getBlocksByType: vi.fn((type: string) => blocks.filter((b) => b.type === type)),
    getAllBlocks: vi.fn(() => [...blocks]),
    setTheme: vi.fn(),
    getGrid: vi.fn(() => null),
    dispose: vi.fn(),
  };

  const emit = (type: string, blockId: string) => {
    if (!listener) throw new Error("useBlocklyWorkspace did not register a change listener");
    listener({ type, blockId, isUiEvent: false } as unknown as Blockly.Events.Abstract);
  };

  return {
    ws,
    /** Adds a block the way Blockly does: the block exists, then BLOCK_CREATE fires. */
    create(block: FakeBlock) {
      blocks.push(block);
      block.dispose.mockImplementation(() => blocks.splice(blocks.indexOf(block), 1));
      emit(Blockly.Events.BLOCK_CREATE, block.id);
    },
    remove(block: FakeBlock) {
      blocks.splice(blocks.indexOf(block), 1);
      emit(Blockly.Events.BLOCK_DELETE, block.id);
    },
  };
}

function renderWorkspaceHook() {
  const fake = createFakeWorkspace();
  vi.mocked(Blockly.inject).mockReturnValue(fake.ws as unknown as Blockly.WorkspaceSvg);
  const hook = renderHook(() => {
    const result = useBlocklyWorkspace();
    // initWorkspace bails out without a container, so attach one before effects run.
    if (!result.containerRef.current) {
      (result.containerRef as { current: HTMLDivElement }).current = document.createElement("div");
    }
    return result;
  });
  return { ...fake, hook };
}

describe("useBlocklyWorkspace change listener", () => {
  beforeEach(() => {
    localStorage.clear();
    usePipelineStore.getState().reset();
    usePipelineStore.setState({ blockCount: 0, uniqueBlockTypes: 0, categoryCounts: {} });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("updates the block count when a non-singleton block is created", () => {
    const { create, ws } = renderWorkspaceHook();
    expect(ws.addChangeListener).toHaveBeenCalledTimes(1);

    create(fakeBlock("gray-1", "imageconversions_graytheimage"));
    expect(usePipelineStore.getState().blockCount).toBe(1);

    create(fakeBlock("blur-1", "blurring_applyblur"));
    expect(usePipelineStore.getState().blockCount).toBe(2);
    expect(usePipelineStore.getState().uniqueBlockTypes).toBe(2);
  });

  it("marks the workspace dirty and schedules an autosave for a non-singleton block", () => {
    vi.useFakeTimers();
    const { create, ws } = renderWorkspaceHook();
    usePipelineStore.setState({ stepResults: [{ index: 0 } as StepResult] });

    create(fakeBlock("gray-1", "imageconversions_graytheimage"));

    expect(usePipelineStore.getState().workspaceDirty).toBe(true);
    vi.mocked(Blockly.serialization.workspaces.save).mockClear();
    vi.advanceTimersByTime(500);
    expect(Blockly.serialization.workspaces.save).toHaveBeenCalledWith(ws);
  });

  it("keeps the first singleton block and counts it", () => {
    const { create } = renderWorkspaceHook();
    const read = fakeBlock("read-1", "basic_readimage");

    create(read);

    expect(read.dispose).not.toHaveBeenCalled();
    expect(usePipelineStore.getState().blockCount).toBe(1);
  });

  it("disposes a duplicate singleton block and leaves it out of the count", () => {
    const { create } = renderWorkspaceHook();
    const first = fakeBlock("read-1", "basic_readimage");
    const duplicate = fakeBlock("read-2", "basic_readimage");

    create(first);
    create(duplicate);

    expect(first.dispose).not.toHaveBeenCalled();
    expect(duplicate.dispose).toHaveBeenCalledWith(false);
    expect(usePipelineStore.getState().blockCount).toBe(1);
  });

  it("updates the block count when a block is deleted", () => {
    const { create, remove } = renderWorkspaceHook();
    const gray = fakeBlock("gray-1", "imageconversions_graytheimage");

    create(gray);
    expect(usePipelineStore.getState().blockCount).toBe(1);

    remove(gray);
    expect(usePipelineStore.getState().blockCount).toBe(0);
  });
});
