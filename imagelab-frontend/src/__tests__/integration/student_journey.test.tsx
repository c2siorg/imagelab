/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup, waitFor } from "@testing-library/react";
import { usePipelineStore } from "../../store/pipelineStore";
import StepResultsPane from "../../components/StepResultsPane";
import type { StepResult } from "../../types/pipeline";
import {
  mockCanvasContext,
  mockScrollIntoView,
  restoreScrollIntoView,
  cleanupMocks,
} from "./test-utils";

// Mock the useStepInspection hook to control async behavior
const mockInspectStep = vi.fn(async (step: StepResult) => {
  const { setActiveStep, setActiveStepAnalysis, setActiveStepHistogram, setActiveStepImage } =
    usePipelineStore.getState();
  setActiveStep(step.block_id ?? null, step.index);
  setActiveStepImage("mock-image-data", "png");
  setActiveStepAnalysis({
    width: 100,
    height: 100,
    channels: 3,
    dtype: "uint8",
    min: 0,
    max: 255,
    mean: [128, 128, 128],
    std: [50, 50, 50],
  });
  setActiveStepHistogram({
    bins: Array.from({ length: 256 }, (_, i) => i),
    luminance: Array.from({ length: 256 }, () => 100),
    red: Array.from({ length: 256 }, () => 50),
    green: Array.from({ length: 256 }, () => 75),
    blue: Array.from({ length: 256 }, () => 25),
  });
  return null;
});

vi.mock("../../hooks/useStepInspection", () => ({
  useStepInspection: () => mockInspectStep,
}));

describe("Student Journey Integration Tests", () => {
  beforeEach(() => {
    mockCanvasContext();
    mockScrollIntoView();
    vi.clearAllMocks();
    mockInspectStep.mockClear();
  });

  afterEach(() => {
    cleanup();
    cleanupMocks();
    restoreScrollIntoView();
    // Reset store state
    usePipelineStore.setState({
      stepResults: [],
      activeStepBlockId: null,
      activeStepIndex: null,
      activeStepImage: null,
      activeStepAnalysis: null,
      activeStepHistogram: null,
      isInspectingStep: false,
      executionId: "test-execution-id",
    });
  });

  describe("Step Results Rendering", () => {
    it("renders_step_thumbnails_after_pipeline_execution", () => {
      // Set up mock step results
      const mockStepResults: StepResult[] = [
        {
          index: 1,
          type: "blurring_applygaussianblur",
          block_id: "blur_1",
          success: true,
          timing_ms: 5.2,
          thumbnail:
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==", // 1x1 red pixel
          image_format: "png",
          has_full_image: true,
        },
      ];

      usePipelineStore.setState({
        stepResults: mockStepResults,
        executionId: "test-execution-id",
      });

      // Render StepResultsPane with null workspace (simpler test)
      render(<StepResultsPane workspace={null} />);

      // Assert step cards are visible
      expect(screen.getByText("Step 1")).toBeDefined();

      // Assert operator labels are visible
      expect(screen.getByText("applygaussianblur")).toBeDefined();

      // Assert timing information is visible
      expect(screen.getByText("5.2 ms")).toBeDefined();
    });

    it("shows_empty_state_when_no_step_results", () => {
      usePipelineStore.setState({
        stepResults: [],
        executionId: null,
      });

      render(<StepResultsPane workspace={null} />);

      expect(screen.getByText("Run the pipeline to see step results")).toBeDefined();
    });
  });

  describe("Step Inspection Flow", () => {
    it("clicking_step_card_updates_active_step_and_loads_analysis", async () => {
      // Set up mock step results
      const mockStepResults: StepResult[] = [
        {
          index: 1,
          type: "blurring_applygaussianblur",
          block_id: "blur_1",
          success: true,
          timing_ms: 5.2,
          thumbnail:
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
          image_format: "png",
          has_full_image: true,
        },
      ];

      usePipelineStore.setState({
        stepResults: mockStepResults,
        executionId: "test-execution-id",
        activeStepBlockId: null,
        activeStepIndex: null,
      });

      // Render StepResultsPane with null workspace to avoid Blockly complexity
      render(<StepResultsPane workspace={null} />);

      // Find the step card (button containing "Step 1")
      const stepCard = screen.getByText("Step 1").closest("button");
      expect(stepCard).toBeDefined();

      // Click the step card
      if (stepCard) {
        fireEvent.click(stepCard);
      }

      // Wait for async operations to complete
      await waitFor(() => {
        const state = usePipelineStore.getState();
        expect(state.activeStepBlockId).toBe("blur_1");
        expect(state.activeStepIndex).toBe(1);
      });

      // Assert that analysis data was loaded
      const state = usePipelineStore.getState();
      expect(state.activeStepAnalysis).not.toBeNull();
      expect(state.activeStepHistogram).not.toBeNull();
      expect(state.activeStepImage).not.toBeNull();

      // Assert histogram data structure
      expect(state.activeStepHistogram?.bins).toHaveLength(256);
      expect(state.activeStepHistogram?.luminance).toHaveLength(256);
      expect(state.activeStepHistogram?.red).toHaveLength(256);
      expect(state.activeStepHistogram?.green).toHaveLength(256);
      expect(state.activeStepHistogram?.blue).toHaveLength(256);

      // Assert analysis data structure
      expect(state.activeStepAnalysis?.width).toBe(100);
      expect(state.activeStepAnalysis?.height).toBe(100);
      expect(state.activeStepAnalysis?.channels).toBe(3);
    });
  });

  describe("Error Handling", () => {
    it("displays_failed_step_cards_with_error_state", () => {
      const mockStepResults: StepResult[] = [
        {
          index: 1,
          type: "blurring_applygaussianblur",
          block_id: "blur_1",
          success: false,
          timing_ms: 2.5,
          thumbnail: null,
          image_format: "png",
          has_full_image: false,
          error: "Invalid kernel size",
        },
      ];

      usePipelineStore.setState({
        stepResults: mockStepResults,
        executionId: "test-execution-id",
      });

      render(<StepResultsPane workspace={null} />);

      // Assert error state is displayed
      expect(screen.getByText("Step 1")).toBeDefined();
      expect(screen.getByText(/Invalid kernel size/)).toBeDefined();

      // Failed step card should have error styling
      const stepCard = screen.getByText("Step 1").closest("button");
      expect(stepCard?.className).toContain("border-red-300");
    });
  });
});
