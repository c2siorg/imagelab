/**
 * @vitest-environment jsdom
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type * as Blockly from "blockly";
import CanvasRoiAnnotator from "../../src/components/Preview/CanvasRoiAnnotator";

describe("CanvasRoiAnnotator Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  afterEach(() => {
    cleanup();
  });

  const dummyImageSrc =
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";

  it("renders with header, aspect ratio presets, and base image", () => {
    render(<CanvasRoiAnnotator imageSrc={dummyImageSrc} naturalWidth={800} naturalHeight={600} />);

    expect(screen.getByText("ROI")).toBeTruthy();
    expect(screen.getByText("1:1")).toBeTruthy();
    expect(screen.getByText("4:3")).toBeTruthy();
    expect(screen.getByText("16:9")).toBeTruthy();
  });

  it("renders with initial bounding box and HUD coordinates", () => {
    const initialBox = { x1: 50, y1: 50, x2: 250, y2: 200 };

    render(
      <CanvasRoiAnnotator
        imageSrc={dummyImageSrc}
        naturalWidth={800}
        naturalHeight={600}
        initialBox={initialBox}
      />,
    );

    // Coordinate badges should reflect initial box
    expect(screen.getByText("200 × 150 px")).toBeTruthy();
    expect(screen.getByText("(50, 50)")).toBeTruthy();
    expect(screen.getByText("Apply to Block")).toBeTruthy();
  });

  it("switches aspect ratio presets on button click", () => {
    render(<CanvasRoiAnnotator imageSrc={dummyImageSrc} naturalWidth={800} naturalHeight={600} />);

    const squareBtn = screen.getByText("1:1");
    fireEvent.click(squareBtn);

    // Square button should now have active styling class
    expect(squareBtn.className).toContain("text-indigo-600");

    const wideBtn = screen.getByText("16:9");
    fireEvent.click(wideBtn);
    expect(wideBtn.className).toContain("text-indigo-600");
  });

  it("copies formatted coordinates to clipboard on copy button click", async () => {
    const initialBox = { x1: 100, y1: 120, x2: 300, y2: 280 };

    render(
      <CanvasRoiAnnotator
        imageSrc={dummyImageSrc}
        naturalWidth={800}
        naturalHeight={600}
        initialBox={initialBox}
      />,
    );

    const copyBtn = screen.getByTitle("Copy coordinates JSON to clipboard");
    fireEvent.click(copyBtn);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      JSON.stringify({ x: 100, y: 120, width: 200, height: 160 }, null, 2),
    );
  });

  it("nudges bounding box on Arrow keys and Shift+Arrow keys", () => {
    const onBoxChange = vi.fn();
    const initialBox = { x1: 100, y1: 100, x2: 200, y2: 200 };

    const { container } = render(
      <CanvasRoiAnnotator
        imageSrc={dummyImageSrc}
        naturalWidth={800}
        naturalHeight={600}
        initialBox={initialBox}
        onBoxChange={onBoxChange}
      />,
    );

    const region = container.querySelector('[role="region"]');
    expect(region).toBeTruthy();

    if (region) {
      fireEvent.keyDown(region, { key: "ArrowRight", shiftKey: false });
      expect(onBoxChange).toHaveBeenCalledWith({ x1: 101, y1: 100, x2: 201, y2: 200 });

      fireEvent.keyDown(region, { key: "ArrowDown", shiftKey: true });
      expect(onBoxChange).toHaveBeenCalledWith({ x1: 101, y1: 110, x2: 201, y2: 210 });
    }
  });

  it("clears bounding box on Escape key or clear button click", () => {
    const onBoxChange = vi.fn();
    const initialBox = { x1: 100, y1: 100, x2: 200, y2: 200 };

    render(
      <CanvasRoiAnnotator
        imageSrc={dummyImageSrc}
        naturalWidth={800}
        naturalHeight={600}
        initialBox={initialBox}
        onBoxChange={onBoxChange}
      />,
    );

    const clearBtn = screen.getByTitle("Clear selection (Esc)");
    fireEvent.click(clearBtn);

    expect(onBoxChange).toHaveBeenCalledWith(null);
  });

  it("applies ROI values to a selected Crop block in workspace", () => {
    const mockBlock = {
      type: "geometric_cropimage",
      setFieldValue: vi.fn(),
    };

    const mockWorkspace = {
      getAllBlocks: vi.fn().mockReturnValue([mockBlock]),
    } as unknown as Blockly.WorkspaceSvg;

    const initialBox = { x1: 10, y1: 20, x2: 110, y2: 140 };

    render(
      <CanvasRoiAnnotator
        imageSrc={dummyImageSrc}
        naturalWidth={800}
        naturalHeight={600}
        initialBox={initialBox}
        workspace={mockWorkspace}
      />,
    );

    const applyBtn = screen.getByText("Apply to Block");
    fireEvent.click(applyBtn);

    expect(mockBlock.setFieldValue).toHaveBeenCalledWith("10", "x1");
    expect(mockBlock.setFieldValue).toHaveBeenCalledWith("20", "y1");
    expect(mockBlock.setFieldValue).toHaveBeenCalledWith("110", "x2");
    expect(mockBlock.setFieldValue).toHaveBeenCalledWith("140", "y2");
  });

  it("displays informational message when no spatial block is present", () => {
    const mockWorkspace = {
      getAllBlocks: vi.fn().mockReturnValue([]),
    } as unknown as Blockly.WorkspaceSvg;

    const initialBox = { x1: 10, y1: 20, x2: 110, y2: 140 };

    render(
      <CanvasRoiAnnotator
        imageSrc={dummyImageSrc}
        naturalWidth={800}
        naturalHeight={600}
        initialBox={initialBox}
        workspace={mockWorkspace}
      />,
    );

    const applyBtn = screen.getByText("Apply to Block");
    fireEvent.click(applyBtn);

    expect(screen.getByText(/No Crop or Rectangle blocks found/i)).toBeTruthy();
  });

  it("normalizes and rounds inverted or fractional coordinates when applying to block", () => {
    const mockBlock = {
      type: "geometric_cropimage",
      setFieldValue: vi.fn(),
    };

    const mockWorkspace = {
      getAllBlocks: vi.fn().mockReturnValue([mockBlock]),
    } as unknown as Blockly.WorkspaceSvg;

    // Inverted (x1 > x2, y1 > y2) and fractional coordinates
    const initialBox = { x1: 150.8, y1: 200.2, x2: 25.1, y2: 50.9 };

    render(
      <CanvasRoiAnnotator
        imageSrc={dummyImageSrc}
        naturalWidth={800}
        naturalHeight={600}
        initialBox={initialBox}
        workspace={mockWorkspace}
      />,
    );

    const applyBtn = screen.getByText("Apply to Block");
    fireEvent.click(applyBtn);

    // Should normalize so x1 <= x2 and y1 <= y2, and round to integers
    expect(mockBlock.setFieldValue).toHaveBeenCalledWith("25", "x1");
    expect(mockBlock.setFieldValue).toHaveBeenCalledWith("51", "y1");
    expect(mockBlock.setFieldValue).toHaveBeenCalledWith("151", "x2");
    expect(mockBlock.setFieldValue).toHaveBeenCalledWith("200", "y2");
  });
});
