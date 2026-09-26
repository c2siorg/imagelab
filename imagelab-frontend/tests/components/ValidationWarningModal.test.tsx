/**
 * @vitest-environment jsdom
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import ValidationWarningModal from "../../src/components/ValidationWarningModal";
import type { ValidationWarning } from "../../src/utils/validatePipelineGraph";

describe("ValidationWarningModal Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  const sampleWarnings: ValidationWarning[] = [
    {
      nodeId: "node-1",
      nodeType: "imageconvertions_grayimage",
      message: "Channel count mismatch: operator expects 3 or 4 channels but received 1 channel.",
      port: "image",
    },
    {
      nodeId: "node-2",
      nodeType: "merge_images",
      message: "Mask input requires 1 channel but received 3 channels.",
      port: "mask",
    },
  ];

  it("renders with title and warnings when open", () => {
    const onRunAnyway = vi.fn();
    const onCancel = vi.fn();

    render(
      <ValidationWarningModal
        isOpen={true}
        warnings={sampleWarnings}
        onRunAnyway={onRunAnyway}
        onCancel={onCancel}
      />,
    );

    expect(screen.getByText("Pipeline Validation Warnings")).toBeTruthy();
    expect(screen.getByText("We found 2 potential issues with your pipeline:")).toBeTruthy();
    expect(
      screen.getByText(
        "Channel count mismatch: operator expects 3 or 4 channels but received 1 channel.",
      ),
    ).toBeTruthy();
    expect(screen.getByText("Block ID: node-1")).toBeTruthy();
    expect(screen.getByText("Mask input requires 1 channel but received 3 channels.")).toBeTruthy();
    expect(screen.getByText("Block ID: node-2")).toBeTruthy();
  });

  it("renders singular text when only one warning exists", () => {
    const onRunAnyway = vi.fn();
    const onCancel = vi.fn();

    render(
      <ValidationWarningModal
        isOpen={true}
        warnings={[sampleWarnings[0]]}
        onRunAnyway={onRunAnyway}
        onCancel={onCancel}
      />,
    );

    expect(screen.getByText("We found a potential issue with your pipeline:")).toBeTruthy();
  });

  it("does not render when isOpen is false", () => {
    const onRunAnyway = vi.fn();
    const onCancel = vi.fn();

    render(
      <ValidationWarningModal
        isOpen={false}
        warnings={sampleWarnings}
        onRunAnyway={onRunAnyway}
        onCancel={onCancel}
      />,
    );

    expect(screen.queryByRole("alertdialog")).toBeNull();
  });

  it("autofocuses the 'Cancel and Fix' button when opened", () => {
    const onRunAnyway = vi.fn();
    const onCancel = vi.fn();

    render(
      <ValidationWarningModal
        isOpen={true}
        warnings={sampleWarnings}
        onRunAnyway={onRunAnyway}
        onCancel={onCancel}
      />,
    );

    const cancelButton = screen.getByRole("button", { name: "Cancel and Fix" });
    expect(document.activeElement).toBe(cancelButton);
  });

  it("calls onCancel when 'Cancel and Fix' button is clicked", () => {
    const onRunAnyway = vi.fn();
    const onCancel = vi.fn();

    render(
      <ValidationWarningModal
        isOpen={true}
        warnings={sampleWarnings}
        onRunAnyway={onRunAnyway}
        onCancel={onCancel}
      />,
    );

    const cancelButton = screen.getByRole("button", { name: "Cancel and Fix" });
    fireEvent.click(cancelButton);

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onRunAnyway).not.toHaveBeenCalled();
  });

  it("calls onRunAnyway when 'Run Anyway' button is clicked", () => {
    const onRunAnyway = vi.fn();
    const onCancel = vi.fn();

    render(
      <ValidationWarningModal
        isOpen={true}
        warnings={sampleWarnings}
        onRunAnyway={onRunAnyway}
        onCancel={onCancel}
      />,
    );

    const runAnywayButton = screen.getByRole("button", { name: "Run Anyway" });
    fireEvent.click(runAnywayButton);

    expect(onRunAnyway).toHaveBeenCalledTimes(1);
    expect(onCancel).not.toHaveBeenCalled();
  });

  it("calls onCancel when close (X) button is clicked", () => {
    const onRunAnyway = vi.fn();
    const onCancel = vi.fn();

    render(
      <ValidationWarningModal
        isOpen={true}
        warnings={sampleWarnings}
        onRunAnyway={onRunAnyway}
        onCancel={onCancel}
      />,
    );

    const closeBtn = screen.getByRole("button", { name: "Close" });
    fireEvent.click(closeBtn);

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onRunAnyway).not.toHaveBeenCalled();
  });

  it("calls onCancel when Escape key is pressed", () => {
    const onRunAnyway = vi.fn();
    const onCancel = vi.fn();

    render(
      <ValidationWarningModal
        isOpen={true}
        warnings={sampleWarnings}
        onRunAnyway={onRunAnyway}
        onCancel={onCancel}
      />,
    );

    fireEvent.keyDown(document, { key: "Escape" });

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onRunAnyway).not.toHaveBeenCalled();
  });

  it("calls onCancel when backdrop is clicked", () => {
    const onRunAnyway = vi.fn();
    const onCancel = vi.fn();

    const { container } = render(
      <ValidationWarningModal
        isOpen={true}
        warnings={sampleWarnings}
        onRunAnyway={onRunAnyway}
        onCancel={onCancel}
      />,
    );

    const backdrop = container.querySelector('[role="presentation"]') as HTMLElement;
    fireEvent.click(backdrop);

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onRunAnyway).not.toHaveBeenCalled();
  });

  it("does not call onCancel when modal content is clicked", () => {
    const onRunAnyway = vi.fn();
    const onCancel = vi.fn();

    render(
      <ValidationWarningModal
        isOpen={true}
        warnings={sampleWarnings}
        onRunAnyway={onRunAnyway}
        onCancel={onCancel}
      />,
    );

    const dialog = screen.getByRole("alertdialog");
    fireEvent.click(dialog);

    expect(onCancel).not.toHaveBeenCalled();
    expect(onRunAnyway).not.toHaveBeenCalled();
  });

  it("renders warnings without nodeId if nodeId is empty", () => {
    const onRunAnyway = vi.fn();
    const onCancel = vi.fn();

    const warningsWithoutNodeId: ValidationWarning[] = [
      {
        nodeId: "",
        nodeType: "",
        message: 'No "Read Image" block found.',
      },
    ];

    render(
      <ValidationWarningModal
        isOpen={true}
        warnings={warningsWithoutNodeId}
        onRunAnyway={onRunAnyway}
        onCancel={onCancel}
      />,
    );

    expect(screen.getByText('No "Read Image" block found.')).toBeTruthy();
    expect(screen.queryByText(/Block ID:/)).toBeNull();
  });
});
