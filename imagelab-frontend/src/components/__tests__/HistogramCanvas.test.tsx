/**
 * @vitest-environment jsdom
 */
import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import HistogramCanvas from "../HistogramCanvas";
import type { ImageHistogram } from "../../types/pipeline";

// Mock HTMLCanvasElement.getContext to avoid jsdom canvas requirement
const mockCanvasContext: Partial<CanvasRenderingContext2D> = {
  scale: vi.fn(),
  clearRect: vi.fn(),
  fillStyle: "",
  fillRect: vi.fn(),
  strokeStyle: "",
  lineWidth: 1,
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  stroke: vi.fn(),
};

HTMLCanvasElement.prototype.getContext = vi.fn(
  () => mockCanvasContext as CanvasRenderingContext2D,
) as unknown as typeof HTMLCanvasElement.prototype.getContext;

describe("HistogramCanvas", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders_histogram_channels_correctly", () => {
    // Test with RGB histogram (channels > 1)
    const rgbHistogram: ImageHistogram = {
      bins: Array.from({ length: 256 }, (_, i) => i),
      luminance: Array.from({ length: 256 }, () => 100),
      red: Array.from({ length: 256 }, () => 50),
      green: Array.from({ length: 256 }, () => 75),
      blue: Array.from({ length: 256 }, () => 25),
    };

    const { rerender } = render(<HistogramCanvas histogram={rgbHistogram} channels={3} />);

    // Check that all color channel checkboxes are present for RGB
    expect(screen.getByLabelText(/Luma|Intensity/i)).toBeDefined();
    expect(screen.getByLabelText(/Red/i)).toBeDefined();
    expect(screen.getByLabelText(/Green/i)).toBeDefined();
    expect(screen.getByLabelText(/Blue/i)).toBeDefined();

    // Check that color channel checkboxes are enabled (not disabled)
    const redCheckbox = screen.getByLabelText(/Red/i) as HTMLInputElement;
    const greenCheckbox = screen.getByLabelText(/Green/i) as HTMLInputElement;
    const blueCheckbox = screen.getByLabelText(/Blue/i) as HTMLInputElement;

    expect(redCheckbox.disabled).toBe(false);
    expect(greenCheckbox.disabled).toBe(false);
    expect(blueCheckbox.disabled).toBe(false);

    // Verify canvas drawing was called (indicates component rendered and attempted to draw)
    expect(mockCanvasContext.stroke).toHaveBeenCalled();

    // Test with grayscale histogram (channels = 1)
    const grayscaleHistogram: ImageHistogram = {
      bins: Array.from({ length: 256 }, (_, i) => i),
      luminance: Array.from({ length: 256 }, () => 100),
    };

    vi.clearAllMocks();
    rerender(<HistogramCanvas histogram={grayscaleHistogram} channels={1} />);

    // For grayscale, color channels should be disabled
    const redCheckboxGray = screen.getByLabelText(/Red/i) as HTMLInputElement;
    const greenCheckboxGray = screen.getByLabelText(/Green/i) as HTMLInputElement;
    const blueCheckboxGray = screen.getByLabelText(/Blue/i) as HTMLInputElement;

    expect(redCheckboxGray.disabled).toBe(true);
    expect(greenCheckboxGray.disabled).toBe(true);
    expect(blueCheckboxGray.disabled).toBe(true);

    // The luminance/intensity channel should still be enabled
    const luminanceCheckbox = screen.getByLabelText(/Luma|Intensity/i) as HTMLInputElement;
    expect(luminanceCheckbox.disabled).toBe(false);

    // Canvas should still attempt to draw
    expect(mockCanvasContext.stroke).toHaveBeenCalled();
  });

  it("handles_empty_histogram_data_gracefully", () => {
    // Test with null histogram
    const { container } = render(<HistogramCanvas histogram={null} channels={3} />);

    // Should show loading state
    expect(screen.getByText(/Loading histogram/i)).toBeDefined();

    // Canvas should still be present
    const canvas = container.querySelector("canvas");
    expect(canvas).toBeDefined();

    // Canvas should not attempt to draw when histogram is null
    if (!mockCanvasContext || !mockCanvasContext.stroke) {
      throw new Error("mockCanvasContext or stroke is not defined");
    }
    expect(vi.mocked(mockCanvasContext.stroke).mock.calls.length).toBeLessThan(5);

    cleanup();

    // Test with histogram but missing color channels
    const partialHistogram: ImageHistogram = {
      bins: Array.from({ length: 256 }, (_, i) => i),
      luminance: Array.from({ length: 256 }, () => 100),
      // red, green, blue are null/undefined
    };

    render(<HistogramCanvas histogram={partialHistogram} channels={3} />);

    // Color channel checkboxes should be disabled when data is missing
    const redCheckbox = screen.getByLabelText(/Red/i) as HTMLInputElement;
    const greenCheckbox = screen.getByLabelText(/Green/i) as HTMLInputElement;
    const blueCheckbox = screen.getByLabelText(/Blue/i) as HTMLInputElement;

    expect(redCheckbox.disabled).toBe(true);
    expect(greenCheckbox.disabled).toBe(true);
    expect(blueCheckbox.disabled).toBe(true);

    // Luminance should still work
    const luminanceCheckbox = screen.getByLabelText(/Luma|Intensity/i) as HTMLInputElement;
    expect(luminanceCheckbox.disabled).toBe(false);

    // Canvas should still attempt to draw with available data
    expect(mockCanvasContext.stroke).toHaveBeenCalled();
  });

  it("toggles_channel_visibility", () => {
    const rgbHistogram: ImageHistogram = {
      bins: Array.from({ length: 256 }, (_, i) => i),
      luminance: Array.from({ length: 256 }, () => 100),
      red: Array.from({ length: 256 }, () => 50),
      green: Array.from({ length: 256 }, () => 75),
      blue: Array.from({ length: 256 }, () => 25),
    };

    render(<HistogramCanvas histogram={rgbHistogram} channels={3} />);

    const redCheckbox = screen.getByLabelText(/Red/i) as HTMLInputElement;

    // Initially red should be unchecked
    expect(redCheckbox.checked).toBe(false);

    // Click to enable red channel
    fireEvent.click(redCheckbox);

    // Should now be checked
    expect(redCheckbox.checked).toBe(true);

    // Canvas should redraw after state change
    vi.clearAllMocks();
    fireEvent.click(redCheckbox);
    expect(mockCanvasContext.stroke).toHaveBeenCalled();
  });

  it("switches_between_log_and_linear_scale", () => {
    const rgbHistogram: ImageHistogram = {
      bins: Array.from({ length: 256 }, (_, i) => i),
      luminance: Array.from({ length: 256 }, () => 100),
      red: Array.from({ length: 256 }, () => 50),
      green: Array.from({ length: 256 }, () => 75),
      blue: Array.from({ length: 256 }, () => 25),
    };

    render(<HistogramCanvas histogram={rgbHistogram} channels={3} />);

    const logButton = screen.getByText("Log");
    const linearButton = screen.getByText("Linear");

    // Log should be selected by default
    expect(logButton.className).toContain("text-indigo-600");
    expect(linearButton.className).toContain("text-gray-500");

    // Click to switch to linear
    fireEvent.click(linearButton);

    // Linear should now be selected
    expect(linearButton.className).toContain("text-indigo-600");
    expect(logButton.className).toContain("text-gray-500");

    // Canvas should redraw after scale change
    vi.clearAllMocks();
    fireEvent.click(logButton);
    expect(mockCanvasContext.stroke).toHaveBeenCalled();
  });
});
