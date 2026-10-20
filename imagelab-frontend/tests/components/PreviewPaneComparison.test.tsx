/**
 * @vitest-environment jsdom
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import PreviewPane from "../../src/components/Preview/PreviewPane";
import { usePipelineStore } from "../../src/store/pipelineStore";

describe("PreviewPane Integration Suite", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    usePipelineStore.setState({
      originalImage: null,
      processedImage: null,
      activeStepImage: null,
      activeStepIndex: null,
      isInspectingStep: false,
      imageFormat: "png",
      error: null,
      errorStep: null,
      timings: null,
    });
  });

  afterEach(() => {
    cleanup();
  });

  const dummyImageA =
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";
  const dummyImageB =
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=";

  it("renders both Original and Processed cards in standard w-80 layout", () => {
    const { container } = render(<PreviewPane />);

    expect(screen.getByText("Original")).toBeTruthy();
    expect(screen.getByText("Processed")).toBeTruthy();
    expect(container.firstChild).toHaveProperty("className");
    expect((container.firstChild as HTMLElement).className).toContain("w-80");
  });

  it("toggles inline ROI Tool on Original card when Crop button is clicked", () => {
    usePipelineStore.setState({
      originalImage: dummyImageA,
    });

    render(<PreviewPane />);

    const roiToggle = screen.getByTitle("Interactive Canvas ROI Selection");
    expect(roiToggle).toBeTruthy();

    fireEvent.click(roiToggle);

    expect(screen.getByText("ROI")).toBeTruthy();
    expect(screen.getByText("1:1")).toBeTruthy();
    expect(screen.getByText("4:3")).toBeTruthy();
    expect(screen.getByText("16:9")).toBeTruthy();
  });

  it("toggles inline Comparison Slider on Processed card when Compare button is clicked", () => {
    usePipelineStore.setState({
      originalImage: dummyImageA,
      processedImage: dummyImageB,
    });

    render(<PreviewPane />);

    const compareToggle = screen.getByTitle(
      "Inline Before/After Split Comparison & Difference Heatmap",
    );
    expect(compareToggle).toBeTruthy();

    fireEvent.click(compareToggle);

    expect(screen.getByText("Split")).toBeTruthy();
    expect(screen.getByText("Diff")).toBeTruthy();
    expect(screen.getByText("Hold")).toBeTruthy();
  });

  it("toggles Pixel Inspector overlay when Crosshair button is clicked", () => {
    usePipelineStore.setState({
      originalImage: dummyImageA,
      processedImage: dummyImageB,
    });

    render(<PreviewPane />);

    const inspectorToggle = screen.getByTitle("Pixel Inspector & 5x5 Neighborhood Grid");
    expect(inspectorToggle).toBeTruthy();

    fireEvent.click(inspectorToggle);
    expect(inspectorToggle.className).toContain("text-indigo-600");
  });

  it("displays step inspection label in Processed card header when inspecting step", () => {
    usePipelineStore.setState({
      originalImage: dummyImageA,
      activeStepImage: dummyImageB,
      activeStepIndex: 3,
      isInspectingStep: true,
    });

    render(<PreviewPane />);

    expect(screen.getByText("Step 3")).toBeTruthy();
  });

  it("disables Compare button when no processed output is present", () => {
    usePipelineStore.setState({
      originalImage: dummyImageA,
      processedImage: null,
    });

    render(<PreviewPane />);

    const compareToggle = screen.getByTitle(
      "Inline Before/After Split Comparison & Difference Heatmap",
    );
    expect((compareToggle as HTMLButtonElement).disabled).toBe(true);
  });

  it("opens click-to-enlarge ImageModal when clicking on original or processed image", () => {
    usePipelineStore.setState({
      originalImage: dummyImageA,
      processedImage: dummyImageB,
      imageFormat: "png",
    });

    render(<PreviewPane />);

    const originalImg = screen.getByAltText("Original");
    expect(originalImg).toBeTruthy();

    // Clicking image opens ImageModal
    fireEvent.click(originalImg);
    expect(screen.getByAltText("Full screen preview")).toBeTruthy();

    // Closing modal removes full screen preview
    const closeBtn = screen.getByLabelText("Close");
    fireEvent.click(closeBtn);
    expect(screen.queryByAltText("Full screen preview")).toBeNull();
  });

  it("preserves read-only gating and aria-labels for upload and camera buttons", () => {
    // Normal mode (isReadOnly = false): upload/camera hidden in PreviewPane
    usePipelineStore.setState({
      isReadOnly: false,
      originalImage: null,
    });

    const { rerender } = render(<PreviewPane />);
    expect(screen.queryByLabelText("Upload image")).toBeNull();
    expect(screen.queryByLabelText("Capture image")).toBeNull();

    // Read-only mode (isReadOnly = true): upload and camera buttons present with aria-labels
    usePipelineStore.setState({
      isReadOnly: true,
      originalImage: null,
    });
    rerender(<PreviewPane />);

    expect(screen.getByLabelText("Upload image")).toBeTruthy();
    expect(screen.getByLabelText("Capture image")).toBeTruthy();
    expect(screen.getByLabelText("Upload image file")).toBeTruthy();
  });

  it("preserves remove image button and aria-label when an image is present", () => {
    const clearImageMock = vi.fn();
    usePipelineStore.setState({
      originalImage: dummyImageA,
      clearImage: clearImageMock,
    });

    render(<PreviewPane />);

    const removeBtn = screen.getByLabelText("Remove image");
    expect(removeBtn).toBeTruthy();
    expect(removeBtn.getAttribute("title")).toBe("Remove image");

    fireEvent.click(removeBtn);
    expect(clearImageMock).toHaveBeenCalledTimes(1);
  });

  it("uses activeStepImageFormat for data URL when inspecting step", () => {
    usePipelineStore.setState({
      originalImage: dummyImageA,
      activeStepImage: dummyImageB,
      activeStepImageFormat: "webp",
      activeStepIndex: 2,
      isInspectingStep: true,
      imageFormat: "png",
    });

    render(<PreviewPane />);

    const processedImg = screen.getByAltText("Step 2") as HTMLImageElement;
    expect(processedImg).toBeTruthy();
    expect(processedImg.src).toContain("data:image/webp;base64,");
  });
});
