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

    const roiToggle = screen.getByTitle("Interactive Canvas ROI Tool (Crop / Bounding Box)");
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
});
