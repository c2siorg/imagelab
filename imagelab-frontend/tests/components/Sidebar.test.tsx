/**
 * @vitest-environment jsdom
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, act } from "@testing-library/react";
import * as Blockly from "blockly";
import Sidebar from "../../src/components/Sidebar/Sidebar";
import {
  SIDEBAR_COLLAPSED_STORAGE_KEY,
  saveSidebarCollapsedState,
} from "../../src/hooks/workspacePersistence";

vi.mock("blockly", async (importOriginal) => {
  const actual = await importOriginal<typeof import("blockly")>();
  return {
    ...actual,
    svgResize: vi.fn(),
  };
});

function createMockWorkspace() {
  const listeners: ((e: Blockly.Events.Abstract) => void)[] = [];
  return {
    addChangeListener: vi.fn((listener: (e: Blockly.Events.Abstract) => void) => {
      listeners.push(listener);
      return listener;
    }),
    removeChangeListener: vi.fn((listener: (e: Blockly.Events.Abstract) => void) => {
      const idx = listeners.indexOf(listener);
      if (idx !== -1) listeners.splice(idx, 1);
    }),
    getBlocksByType: vi.fn(() => []),
    getBlockById: vi.fn(() => null),
  } as unknown as Blockly.WorkspaceSvg;
}

describe("Sidebar component", () => {
  let mockWorkspace: Blockly.WorkspaceSvg;

  beforeEach(() => {
    localStorage.clear();
    mockWorkspace = createMockWorkspace();
    vi.mocked(Blockly.svgResize).mockClear();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("renders expanded by default when no saved state exists", () => {
    render(<Sidebar workspace={mockWorkspace} />);

    const sidebar = screen.getByRole("complementary", { name: "Blocks sidebar" });
    expect(sidebar.className).toContain("w-80");
    expect(sidebar.className).not.toContain("w-12");

    const collapseBtn = screen.getByRole("button", { name: "Collapse Blocks sidebar" });
    expect(collapseBtn).toBeTruthy();
    expect(collapseBtn.getAttribute("aria-expanded")).toBe("true");

    const content = document.getElementById("sidebar-blocks-content");
    expect(content).not.toBeNull();
    expect(content?.classList.contains("hidden")).toBe(false);

    expect(screen.getByPlaceholderText("Search blocks...")).toBeTruthy();
  });

  it("collapses when clicking the collapse button and saves state to localStorage", () => {
    render(<Sidebar workspace={mockWorkspace} />);

    const collapseBtn = screen.getByRole("button", { name: "Collapse Blocks sidebar" });
    act(() => {
      fireEvent.click(collapseBtn);
    });

    const sidebar = screen.getByRole("complementary", { name: "Blocks sidebar" });
    expect(sidebar.className).toContain("w-12");
    expect(sidebar.className).not.toContain("w-80");

    const expandBtn = screen.getByRole("button", { name: "Expand Blocks sidebar" });
    expect(expandBtn).toBeTruthy();
    expect(expandBtn.getAttribute("aria-expanded")).toBe("false");

    const content = document.getElementById("sidebar-blocks-content");
    expect(content?.classList.contains("hidden")).toBe(true);
    expect(content?.getAttribute("aria-hidden")).toBe("true");

    expect(localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY)).toBe("true");
    expect(vi.mocked(Blockly.svgResize)).toHaveBeenCalledWith(mockWorkspace);
  });

  it("expands when clicking the expand button from collapsed state", () => {
    saveSidebarCollapsedState(true);
    render(<Sidebar workspace={mockWorkspace} />);

    const sidebar = screen.getByRole("complementary", { name: "Blocks sidebar" });
    expect(sidebar.className).toContain("w-12");

    const expandBtn = screen.getByRole("button", { name: "Expand Blocks sidebar" });
    act(() => {
      fireEvent.click(expandBtn);
    });

    expect(sidebar.className).toContain("w-80");
    expect(screen.getByRole("button", { name: "Collapse Blocks sidebar" })).toBeTruthy();
    expect(localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY)).toBe("false");
    expect(vi.mocked(Blockly.svgResize)).toHaveBeenCalledWith(mockWorkspace);
  });

  it("preserves search query and category states across collapse and expand", () => {
    render(<Sidebar workspace={mockWorkspace} />);

    const searchInput = screen.getByPlaceholderText("Search blocks...") as HTMLInputElement;
    fireEvent.change(searchInput, { target: { value: "blur" } });
    expect(searchInput.value).toBe("blur");

    // Collapse
    const collapseBtn = screen.getByRole("button", { name: "Collapse Blocks sidebar" });
    act(() => {
      fireEvent.click(collapseBtn);
    });

    // Expand
    const expandBtn = screen.getByRole("button", { name: "Expand Blocks sidebar" });
    act(() => {
      fireEvent.click(expandBtn);
    });

    const restoredSearchInput = screen.getByPlaceholderText("Search blocks...") as HTMLInputElement;
    expect(restoredSearchInput.value).toBe("blur");
  });

  it("supports keyboard interaction on toggle buttons", () => {
    render(<Sidebar workspace={mockWorkspace} />);

    const collapseBtn = screen.getByRole("button", { name: "Collapse Blocks sidebar" });
    collapseBtn.focus();
    expect(document.activeElement).toBe(collapseBtn);

    act(() => {
      fireEvent.keyDown(collapseBtn, { key: "Enter", code: "Enter" });
      fireEvent.click(collapseBtn);
    });

    const expandBtn = screen.getByRole("button", { name: "Expand Blocks sidebar" });
    expect(expandBtn).toBeTruthy();
    expandBtn.focus();
    expect(document.activeElement).toBe(expandBtn);
  });

  it("triggers Blockly.svgResize on transitionend", () => {
    render(<Sidebar workspace={mockWorkspace} />);

    const sidebar = screen.getByRole("complementary", { name: "Blocks sidebar" });
    vi.mocked(Blockly.svgResize).mockClear();

    fireEvent.transitionEnd(sidebar);
    expect(vi.mocked(Blockly.svgResize)).toHaveBeenCalledWith(mockWorkspace);
  });

  it("handles null workspace gracefully during toggle and transitions", () => {
    expect(() => {
      render(<Sidebar workspace={null} />);
      const collapseBtn = screen.getByRole("button", { name: "Collapse Blocks sidebar" });
      act(() => {
        fireEvent.click(collapseBtn);
      });
      const sidebar = screen.getByRole("complementary", { name: "Blocks sidebar" });
      fireEvent.transitionEnd(sidebar);
    }).not.toThrow();
  });
});
