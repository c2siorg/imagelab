/**
 * @vitest-environment jsdom
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import ImageComparisonSlider from "../../src/components/Preview/ImageComparisonSlider";

describe("ImageComparisonSlider Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  const dummyBefore =
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";
  const dummyAfter =
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=";

  it("renders with default split mode, original and processed labels", () => {
    render(
      <ImageComparisonSlider
        originalSrc={dummyBefore}
        processedSrc={dummyAfter}
        originalLabel="Input Photo"
        processedLabel="Result Photo"
      />,
    );

    expect(screen.getByText("Input Photo")).toBeTruthy();
    expect(screen.getByText("Result Photo")).toBeTruthy();
    expect(screen.getByText("Split")).toBeTruthy();
    expect(screen.getByText("Diff")).toBeTruthy();
    expect(screen.getByText("Hold")).toBeTruthy();
  });

  it("switches to Diff mode and displays colormap selector", () => {
    render(<ImageComparisonSlider originalSrc={dummyBefore} processedSrc={dummyAfter} />);

    const diffBtn = screen.getByText("Diff");
    fireEvent.click(diffBtn);

    // Should render colormap select dropdown
    const select = screen.getByRole("combobox");
    expect(select).toBeTruthy();
    expect(select.children.length).toBe(3); // thermal, jet, grayscale
  });

  it("switches to Hold Before mode and toggles view state", () => {
    render(<ImageComparisonSlider originalSrc={dummyBefore} processedSrc={dummyAfter} />);

    const holdBtn = screen.getByText("Hold");
    fireEvent.click(holdBtn);

    expect(screen.getByText(/Press & Hold to View Original/)).toBeTruthy();
    expect(screen.getByText("Showing: Processed")).toBeTruthy();

    const actionBtn = screen.getByText(/Press & Hold to View Original/);
    fireEvent.mouseDown(actionBtn);
    expect(screen.getByText("Showing: Original")).toBeTruthy();

    fireEvent.mouseUp(actionBtn);
    expect(screen.getByText("Showing: Processed")).toBeTruthy();
  });

  it("toggles hold state when pressing and releasing backslash key", () => {
    render(<ImageComparisonSlider originalSrc={dummyBefore} processedSrc={dummyAfter} />);

    fireEvent.click(screen.getByText("Hold"));
    expect(screen.getByText("Showing: Processed")).toBeTruthy();

    fireEvent.keyDown(window, { key: "\\" });
    expect(screen.getByText("Showing: Original")).toBeTruthy();

    fireEvent.keyUp(window, { key: "\\" });
    expect(screen.getByText("Showing: Processed")).toBeTruthy();
  });

  it("calls onExpand callback when maximize button is clicked", () => {
    const onExpand = vi.fn();
    render(
      <ImageComparisonSlider
        originalSrc={dummyBefore}
        processedSrc={dummyAfter}
        onExpand={onExpand}
      />,
    );

    const expandBtn = screen.getByTitle("Expand full screen");
    fireEvent.click(expandBtn);
    expect(onExpand).toHaveBeenCalledTimes(1);
  });

  it("switches to 2-Up Side-by-Side mode", () => {
    render(
      <ImageComparisonSlider
        originalSrc={dummyBefore}
        processedSrc={dummyAfter}
        originalLabel="Base"
        processedLabel="Result"
      />,
    );

    const sideBtn = screen.getByText("2-Up");
    fireEvent.click(sideBtn);

    expect(screen.getByText("Base")).toBeTruthy();
    expect(screen.getByText("Result")).toBeTruthy();
  });

  it("toggles split wipe orientation between Vert and Horiz", () => {
    render(<ImageComparisonSlider originalSrc={dummyBefore} processedSrc={dummyAfter} />);

    expect(screen.getByText("Vert")).toBeTruthy();
    const orientBtn = screen.getByTitle("Toggle split wipe orientation (vertical / horizontal)");
    fireEvent.click(orientBtn);

    expect(screen.getByText("Horiz")).toBeTruthy();
  });

  it("switches sensitivity gain pills in Diff mode", () => {
    render(<ImageComparisonSlider originalSrc={dummyBefore} processedSrc={dummyAfter} />);

    fireEvent.click(screen.getByText("Diff"));

    expect(screen.getByText("1x")).toBeTruthy();
    expect(screen.getByText("2x")).toBeTruthy();
    expect(screen.getByText("4x")).toBeTruthy();
    expect(screen.getByText("8x")).toBeTruthy();

    const gain4Btn = screen.getByText("4x");
    fireEvent.click(gain4Btn);
    expect(gain4Btn.className).toContain("bg-indigo-600");
  });

  it("toggles auto-blink mode in Hold view", () => {
    render(<ImageComparisonSlider originalSrc={dummyBefore} processedSrc={dummyAfter} />);

    fireEvent.click(screen.getByText("Hold"));
    const blinkBtn = screen.getByTitle("Toggle automatic 1.5 Hz blink comparison");
    expect(blinkBtn).toBeTruthy();

    fireEvent.click(blinkBtn);
    expect(blinkBtn.className).toContain("bg-amber-50");
  });
});
