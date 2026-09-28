/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useWorkspaceDrop } from "../../src/hooks/useWorkspaceDrop";
import { usePipelineStore } from "../../src/store/pipelineStore";

vi.mock("../../src/store/pipelineStore", () => ({
  usePipelineStore: vi.fn(),
}));

describe("useWorkspaceDrop", () => {
  let setOriginalImageMock: ReturnType<typeof vi.fn>;
  let dropZoneEl: HTMLDivElement;
  let childEl: HTMLDivElement;
  let outsideEl: HTMLDivElement;

  beforeEach(() => {
    vi.clearAllMocks();
    setOriginalImageMock = vi.fn();
    (usePipelineStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      setOriginalImage: setOriginalImageMock,
    });

    dropZoneEl = document.createElement("div");
    childEl = document.createElement("div");
    outsideEl = document.createElement("div");

    dropZoneEl.appendChild(childEl);
    document.body.appendChild(dropZoneEl);
    document.body.appendChild(outsideEl);
  });

  it("sets isDragOver to true when dragging files over drop zone", () => {
    const dropZoneRef = { current: dropZoneEl };
    const { result } = renderHook(() => useWorkspaceDrop({ dropZoneRef, enabled: true }));

    expect(result.current.isDragOver).toBe(false);

    act(() => {
      const enterEvent = new Event("dragenter", { bubbles: true }) as DragEvent;
      Object.defineProperty(enterEvent, "dataTransfer", {
        value: { types: ["Files"] },
      });
      dropZoneEl.dispatchEvent(enterEvent);
    });

    expect(result.current.isDragOver).toBe(true);
  });

  it("does not activate isDragOver if dragged item does not contain files", () => {
    const dropZoneRef = { current: dropZoneEl };
    const { result } = renderHook(() => useWorkspaceDrop({ dropZoneRef, enabled: true }));

    act(() => {
      const enterEvent = new Event("dragenter", { bubbles: true }) as DragEvent;
      Object.defineProperty(enterEvent, "dataTransfer", {
        value: { types: ["text/plain"] },
      });
      dropZoneEl.dispatchEvent(enterEvent);
    });

    expect(result.current.isDragOver).toBe(false);
  });

  it("keeps isDragOver true when moving cursor to a child element inside drop zone", () => {
    const dropZoneRef = { current: dropZoneEl };
    const { result } = renderHook(() => useWorkspaceDrop({ dropZoneRef, enabled: true }));

    act(() => {
      const enterEvent = new Event("dragenter", { bubbles: true }) as DragEvent;
      Object.defineProperty(enterEvent, "dataTransfer", {
        value: { types: ["Files"] },
      });
      dropZoneEl.dispatchEvent(enterEvent);
    });

    expect(result.current.isDragOver).toBe(true);

    // Moving from dropZone into child element (relatedTarget is inside dropZone)
    act(() => {
      const leaveEvent = new Event("dragleave", { bubbles: true }) as DragEvent;
      Object.defineProperty(leaveEvent, "relatedTarget", {
        value: childEl,
      });
      dropZoneEl.dispatchEvent(leaveEvent);
    });

    expect(result.current.isDragOver).toBe(true);
  });

  it("sets isDragOver to false when cursor truly leaves drop zone boundary", () => {
    const dropZoneRef = { current: dropZoneEl };
    const { result } = renderHook(() => useWorkspaceDrop({ dropZoneRef, enabled: true }));

    act(() => {
      const enterEvent = new Event("dragenter", { bubbles: true }) as DragEvent;
      Object.defineProperty(enterEvent, "dataTransfer", {
        value: { types: ["Files"] },
      });
      dropZoneEl.dispatchEvent(enterEvent);
    });

    expect(result.current.isDragOver).toBe(true);

    // Moving to outside element
    act(() => {
      const leaveEvent = new Event("dragleave", { bubbles: true }) as DragEvent;
      Object.defineProperty(leaveEvent, "relatedTarget", {
        value: outsideEl,
      });
      dropZoneEl.dispatchEvent(leaveEvent);
    });

    expect(result.current.isDragOver).toBe(false);
  });

  it("sets isDragOver to false when leaving the browser window (relatedTarget is null)", () => {
    const dropZoneRef = { current: dropZoneEl };
    const { result } = renderHook(() => useWorkspaceDrop({ dropZoneRef, enabled: true }));

    act(() => {
      const enterEvent = new Event("dragenter", { bubbles: true }) as DragEvent;
      Object.defineProperty(enterEvent, "dataTransfer", {
        value: { types: ["Files"] },
      });
      dropZoneEl.dispatchEvent(enterEvent);
    });

    expect(result.current.isDragOver).toBe(true);

    act(() => {
      const leaveEvent = new Event("dragleave", { bubbles: true }) as DragEvent;
      Object.defineProperty(leaveEvent, "relatedTarget", {
        value: null,
      });
      dropZoneEl.dispatchEvent(leaveEvent);
    });

    expect(result.current.isDragOver).toBe(false);
  });

  it("does not attach listeners or respond when enabled is false", () => {
    const dropZoneRef = { current: dropZoneEl };
    const { result } = renderHook(() => useWorkspaceDrop({ dropZoneRef, enabled: false }));

    act(() => {
      const enterEvent = new Event("dragenter", { bubbles: true }) as DragEvent;
      Object.defineProperty(enterEvent, "dataTransfer", {
        value: { types: ["Files"] },
      });
      dropZoneEl.dispatchEvent(enterEvent);
    });

    expect(result.current.isDragOver).toBe(false);
  });

  it("works with containerRef fallback when dropZoneRef is not provided", () => {
    const containerRef = { current: dropZoneEl };
    const { result } = renderHook(() => useWorkspaceDrop({ containerRef, enabled: true }));

    act(() => {
      const enterEvent = new Event("dragenter", { bubbles: true }) as DragEvent;
      Object.defineProperty(enterEvent, "dataTransfer", {
        value: { types: ["Files"] },
      });
      dropZoneEl.dispatchEvent(enterEvent);
    });

    expect(result.current.isDragOver).toBe(true);
  });
});
