/**
 * @vitest-environment jsdom
 */
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import * as Blockly from "blockly";
import { useSidebarDrag } from "../../src/hooks/useSidebarDrag";
import { isSingletonBlockPresent } from "../../src/utils/blockLimits";

if (typeof PointerEvent === "undefined") {
  (global as any).PointerEvent = class PointerEvent extends MouseEvent {
    pointerId: number;
    pointerType: string;
    constructor(type: string, params: any = {}) {
      super(type, params);
      this.pointerId = params.pointerId || 0;
      this.pointerType = params.pointerType || "mouse";
    }
  };
}

vi.mock("blockly", () => {
  return {
    utils: {
      Coordinate: function (this: any, x: number, y: number) {
        this.x = x;
        this.y = y;
      },
      svgMath: {
        screenToWsCoordinates: vi.fn(() => ({ x: 0, y: 0 })),
      },
    },
    Events: {
      setGroup: vi.fn(),
      getGroup: vi.fn(() => "mock-group"),
    },
  };
});

vi.mock("../../src/utils/blockLimits", () => ({
  SINGLETON_BLOCK_TYPES: new Set(["singleton_type"]),
  isSingletonBlockPresent: vi.fn(() => false),
}));

describe("useSidebarDrag", () => {
  let mockBlock: any;
  let mockWorkspace: any;

  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    
    // Mock requestAnimationFrame
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((cb) => {
      cb(0);
      return 0;
    });

    mockBlock = {
      initSvg: vi.fn(),
      render: vi.fn(),
      moveTo: vi.fn(),
      startDrag: vi.fn(),
      drag: vi.fn(),
      endDrag: vi.fn(),
      revertDrag: vi.fn(),
      dispose: vi.fn(),
    };

    mockWorkspace = {
      getParentSvg: vi.fn(() => ({
        getBoundingClientRect: vi.fn(() => ({
          left: 0,
          top: 0,
          right: 1000,
          bottom: 1000,
        })),
      })),
      newBlock: vi.fn(() => mockBlock),
      getBlocksByType: vi.fn(() => []),
    };

    document.body.innerHTML = "";
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  const triggerMouseDown = (onMouseDown: any, clientX = 10, clientY = 10) => {
    act(() => {
      onMouseDown({
        button: 0,
        clientX,
        clientY,
      } as any);
    });
  };

  const triggerMouseMove = (clientX: number, clientY: number) => {
    act(() => {
      const event = new MouseEvent("mousemove", { clientX, clientY });
      document.dispatchEvent(event);
      vi.runAllTimers();
    });
  };

  const triggerMouseUp = (clientX: number, clientY: number) => {
    act(() => {
      const event = new MouseEvent("mouseup", { clientX, clientY });
      document.dispatchEvent(event);
    });
  };

  it("should initialize a drag and create a ghost element after threshold", () => {
    const { result } = renderHook(() =>
      useSidebarDrag({
        type: "test_block",
        label: "Test Label",
        workspace: mockWorkspace,
      })
    );

    triggerMouseDown(result.current.onMouseDown);
    triggerMouseMove(50, 50);

    const ghost = document.querySelector(".sidebar-drag-ghost");
    expect(ghost).not.toBeNull();
    expect(ghost?.textContent).toBe("Test Label");
  });

  it("should create a Blockly block when mouse enters workspace", () => {
    const { result } = renderHook(() =>
      useSidebarDrag({
        type: "test_block",
        label: "Test Label",
        workspace: mockWorkspace,
      })
    );

    triggerMouseDown(result.current.onMouseDown);
    triggerMouseMove(50, 50);
    triggerMouseMove(100, 100);

    expect(mockWorkspace.newBlock).toHaveBeenCalledWith("test_block");
    expect(mockBlock.initSvg).toHaveBeenCalled();
    expect(mockBlock.render).toHaveBeenCalled();
    expect(mockBlock.startDrag).toHaveBeenCalled();
    expect(Blockly.Events.setGroup).toHaveBeenCalled();
  });

  it("should call drag on the block while moving over workspace", () => {
    const { result } = renderHook(() =>
      useSidebarDrag({
        type: "test_block",
        label: "Test Label",
        workspace: mockWorkspace,
      })
    );

    triggerMouseDown(result.current.onMouseDown);
    triggerMouseMove(50, 50);
    triggerMouseMove(100, 100);
    triggerMouseMove(150, 150);

    expect(mockBlock.drag).toHaveBeenCalled();
  });

  it("should abort drag and dispose block when mouse leaves workspace", () => {
    const { result } = renderHook(() =>
      useSidebarDrag({
        type: "test_block",
        label: "Test Label",
        workspace: mockWorkspace,
      })
    );

    triggerMouseDown(result.current.onMouseDown);
    triggerMouseMove(50, 50);
    triggerMouseMove(100, 100);
    
    mockWorkspace.getParentSvg.mockReturnValue({
      getBoundingClientRect: () => ({ left: 200, top: 200, right: 300, bottom: 300 }),
    });

    act(() => {
      window.dispatchEvent(new Event("resize"));
    });
    
    triggerMouseMove(50, 50);

    expect(mockBlock.revertDrag).toHaveBeenCalled();
    expect(mockBlock.dispose).toHaveBeenCalled();
  });

  it("should finalize block and close event group on mouseup inside workspace", () => {
    const { result } = renderHook(() =>
      useSidebarDrag({
        type: "test_block",
        label: "Test Label",
        workspace: mockWorkspace,
      })
    );

    triggerMouseDown(result.current.onMouseDown);
    triggerMouseMove(50, 50);
    triggerMouseMove(100, 100);
    
    triggerMouseUp(150, 150);

    expect(mockBlock.endDrag).toHaveBeenCalled();
    expect(mockBlock.dispose).not.toHaveBeenCalled();
    expect(Blockly.Events.setGroup).toHaveBeenCalledWith(false);
    expect(document.querySelector(".sidebar-drag-ghost")).toBeNull();
  });

  it("should not allow creating a block of singleton type if already present", () => {
    vi.mocked(isSingletonBlockPresent).mockReturnValue(true);

    const { result } = renderHook(() =>
      useSidebarDrag({
        type: "singleton_type",
        label: "Singleton",
        workspace: mockWorkspace,
      })
    );

    triggerMouseDown(result.current.onMouseDown);
    triggerMouseMove(50, 50);
    triggerMouseMove(100, 100);

    expect(mockWorkspace.newBlock).not.toHaveBeenCalled();
    expect(document.querySelector(".sidebar-drag-ghost")).not.toBeNull();
  });

  it("should handle startDrag failure and abort cleanly", () => {
    mockBlock.startDrag.mockImplementation(() => {
      throw new Error("startDrag failed");
    });
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    const { result } = renderHook(() =>
      useSidebarDrag({
        type: "test_block",
        label: "Test Label",
        workspace: mockWorkspace,
      })
    );

    triggerMouseDown(result.current.onMouseDown);
    triggerMouseMove(50, 50);
    triggerMouseMove(100, 100);

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining("Failed to create drag block"),
      expect.any(Error)
    );
    expect(mockBlock.dispose).toHaveBeenCalled();
    
    consoleSpy.mockRestore();
  });

  it("should not create a block on mouseup outside workspace", () => {
    const { result } = renderHook(() =>
      useSidebarDrag({
        type: "test_block",
        label: "Test Label",
        workspace: mockWorkspace,
      })
    );

    mockWorkspace.getParentSvg.mockReturnValue({
      getBoundingClientRect: () => ({ left: 500, top: 500, right: 1000, bottom: 1000 }),
    });

    triggerMouseDown(result.current.onMouseDown, 10, 10);
    triggerMouseMove(50, 50); 
    triggerMouseUp(60, 60); 

    expect(mockWorkspace.newBlock).not.toHaveBeenCalled();
    expect(document.querySelector(".sidebar-drag-ghost")).toBeNull();
  });

  it("should clean up Blockly block on unmount", () => {
    const { result, unmount } = renderHook(() =>
      useSidebarDrag({
        type: "test_block",
        label: "Test Label",
        workspace: mockWorkspace,
      })
    );

    triggerMouseDown(result.current.onMouseDown);
    triggerMouseMove(50, 50);
    triggerMouseMove(100, 100); 

    unmount();

    expect(mockBlock.revertDrag).toHaveBeenCalled();
    expect(mockBlock.dispose).toHaveBeenCalled();
    expect(document.querySelector(".sidebar-drag-ghost")).toBeNull();
  });
});
