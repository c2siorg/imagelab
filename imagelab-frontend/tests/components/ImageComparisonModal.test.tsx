/**
 * @vitest-environment jsdom
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import ImageComparisonModal from "../../src/components/Preview/ImageComparisonModal";

describe("ImageComparisonModal Component", () => {
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

  it("renders nothing when isOpen is false", () => {
    const { container } = render(
      <ImageComparisonModal
        isOpen={false}
        onClose={vi.fn()}
        originalSrc={dummyBefore}
        processedSrc={dummyAfter}
      />,
    );

    expect(container.firstChild).toBeNull();
  });

  it("renders comparison modal when isOpen is true", () => {
    render(
      <ImageComparisonModal
        isOpen={true}
        onClose={vi.fn()}
        originalSrc={dummyBefore}
        processedSrc={dummyAfter}
        originalLabel="Input"
        processedLabel="Output"
      />,
    );

    expect(screen.getByText("Comparison Inspector")).toBeTruthy();
    expect(screen.getByText("Input vs Output")).toBeTruthy();
    expect(screen.getByText("Split")).toBeTruthy();
    expect(screen.getByText("2-Up")).toBeTruthy();
    expect(screen.getByText("Diff")).toBeTruthy();
    expect(screen.getByText("Hold")).toBeTruthy();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    render(
      <ImageComparisonModal
        isOpen={true}
        onClose={onClose}
        originalSrc={dummyBefore}
        processedSrc={dummyAfter}
      />,
    );

    const closeBtn = screen.getByTitle("Close dialog (Escape)");
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when Escape key is pressed", () => {
    const onClose = vi.fn();
    render(
      <ImageComparisonModal
        isOpen={true}
        onClose={onClose}
        originalSrc={dummyBefore}
        processedSrc={dummyAfter}
      />,
    );

    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
