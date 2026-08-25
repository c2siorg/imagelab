/**
 * @vitest-environment jsdom
 */
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
  cleanup,
} from "@testing-library/react";
import React from "react";
import BatchProcessingModal from "../src/components/BatchProcessingModal";
import {
  createBatchJob,
  getBatchJobStatus,
  getBatchJobDownloadUrl,
} from "../src/api/batch";

// ---------------------------------------------------------------------------
// Module mock
// ---------------------------------------------------------------------------
vi.mock("../src/api/batch", () => ({
  createBatchJob: vi.fn(),
  getBatchJobStatus: vi.fn(),
  getBatchJobDownloadUrl: vi.fn(
    (jobId: string) =>
      `http://localhost:4100/api/v1/batch-jobs/${encodeURIComponent(jobId)}/download`,
  ),
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------
const mockGraph = {
  nodes: [
    { id: "node1", type: "basic_readimage", op: "basic_readimage", params: { filename_label: "test.png" } },
  ],
  edges: [],
};
const mockOnClose = vi.fn();

const renderModal = () =>
  render(
    React.createElement(BatchProcessingModal, {
      graph: mockGraph,
      onClose: mockOnClose,
    }),
  );

// ---------------------------------------------------------------------------
// flushPromises
//
// Drains the microtask queue through React's act() without relying on any
// timer (setTimeout / setInterval). This is safe to use even when fake timers
// are active, because Promise.resolve() runs as a microtask, not a macro-task.
//
// 6 passes cover the deepest async chain in the component:
//   handleStartBatch  →  createBatchJob resolves  →  setJobId
//   →  useEffect fires  →  poll()  →  getBatchJobStatus resolves  →  setSummary
// ---------------------------------------------------------------------------
const flushPromises = async () => {
  for (let i = 0; i < 6; i++) {
    await act(async () => {
      await Promise.resolve();
    });
  }
};

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------
beforeEach(() => {
  // Unmount any React tree left by the previous test BEFORE resetting mocks.
  cleanup();
  vi.clearAllMocks();

  window.URL.createObjectURL = vi.fn(() => "blob:mock-zip-url");
  window.URL.revokeObjectURL = vi.fn();
  vi.spyOn(window, "alert").mockImplementation(() => { });
  vi.spyOn(HTMLAnchorElement.prototype, "click")
    .mockImplementation(() => { });
});

afterEach(() => {
  cleanup();
  // CRITICAL: always restore real timers here, not inside each test.
  // If a fake-timer test times out, the code inside the test (vi.useRealTimers())
  // never runs, poisoning every subsequent test's waitFor with fake timers.
  vi.useRealTimers();
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("BatchProcessingModal Component Suite", () => {
  // ── 1. Initial render ────────────────────────────────────────────────────
  it("renders the modal in initial setup mode", () => {
    renderModal();

    expect(screen.getByText("Batch Image Processing")).toBeDefined();
    expect(
      screen.getByText(/Run active Blockly pipeline steps on multiple files/),
    ).toBeDefined();

    const formatSelect = screen.getByLabelText(
      "Output Image Format",
    ) as HTMLSelectElement;
    expect(formatSelect.value).toBe("png");

    expect(
      screen.getByText("Drag & drop your images here, or click to browse"),
    ).toBeDefined();

    // Submit disabled with 0 files
    const submitBtn = screen.getByRole("button", {
      name: /Process 0 Images/i,
    }) as HTMLButtonElement;
    expect(submitBtn.disabled).toBe(true);

    // Close button calls onClose
    fireEvent.click(screen.getByLabelText("Close"));
    expect(mockOnClose).toHaveBeenCalled();
  });

  // ── 2. File selection & removal ──────────────────────────────────────────
  it("handles file input changes, displays files, and can remove them", async () => {
    const { container } = renderModal();
    const fileInput = container.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    const file1 = new File(["d1"], "pic1.png", { type: "image/png" });
    const file2 = new File(["d2"], "pic2.jpeg", { type: "image/jpeg" });

    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [file1, file2] } });
    });

    expect(screen.getByText("pic1.png")).toBeDefined();
    expect(screen.getByText("pic2.jpeg")).toBeDefined();

    const twoFilesBtn = screen.getByRole("button", {
      name: /Process 2 Images/i,
    }) as HTMLButtonElement;
    expect(twoFilesBtn.disabled).toBe(false);

    // Remove first file individually
    const removeBtns = screen.getAllByTitle("Remove file");
    expect(removeBtns).toHaveLength(2);
    await act(async () => {
      fireEvent.click(removeBtns[0]);
    });
    expect(screen.queryByText("pic1.png")).toBeNull();
    expect(screen.getByText("pic2.jpeg")).toBeDefined();

    const oneFileBtn = screen.getByRole("button", {
      name: /Process 1 Images/i,
    }) as HTMLButtonElement;
    expect(oneFileBtn.disabled).toBe(false);

    // Remove all
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /Remove All/i }));
    });
    expect(screen.queryByText("pic2.jpeg")).toBeNull();
    const emptyBtn = screen.getByRole("button", {
      name: /Process 0 Images/i,
    }) as HTMLButtonElement;
    expect(emptyBtn.disabled).toBe(true);
  });

  // ── 3. Drag-and-drop ─────────────────────────────────────────────────────
  it("handles drag-and-drop feedback changes", async () => {
    const { container } = renderModal();
    const dropZone = container.querySelector(".relative.h-44")!;

    await act(async () => {
      fireEvent.dragOver(dropZone);
    });
    expect(dropZone.className).toContain("border-indigo-500");

    await act(async () => {
      fireEvent.dragLeave(dropZone);
    });
    expect(dropZone.className).not.toContain("border-indigo-500");

    const file = new File(["x"], "dragged.webp", { type: "image/webp" });
    await act(async () => {
      fireEvent.drop(dropZone, { dataTransfer: { files: [file] } });
    });
    expect(screen.getByText("dragged.webp")).toBeDefined();
  });

  // ── 4. Successful polling cycle ───────────────────────────────────────────
  // Uses fake timers to control the 1-second poll interval.
  // Does NOT use waitFor — waitFor's internal setTimeout deadlocks with fake timers.
  // Instead uses flushPromises() (microtask-based, timer-independent).
  it("starts batch process successfully and polls until completion", async () => {
    vi.useFakeTimers();
    const { container } = renderModal();

    const fileInput = container.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const file1 = new File(["a"], "img1.png", { type: "image/png" });
    const file2 = new File(["b"], "img2.png", { type: "image/png" });
    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [file1, file2] } });
    });

    vi.mocked(createBatchJob).mockResolvedValueOnce({
      job_id: "job-xyz-123",
      status: "pending",
      total_files: 2,
    });
    vi.mocked(getBatchJobStatus)
      .mockResolvedValueOnce({
        job_id: "job-xyz-123",
        status: "processing",
        total_files: 2,
        processed_files: 1,
        success_count: 1,
        failure_count: 0,
        created_at: 1000,
        updated_at: 1001,
        duration_seconds: 0.8,
        results: [
          {
            filename: "img1.png",
            success: true,
            output_filename: "out_img1.png",
            error: null,
          },
        ],
      })
      .mockResolvedValueOnce({
        job_id: "job-xyz-123",
        status: "completed",
        total_files: 2,
        processed_files: 2,
        success_count: 2,
        failure_count: 0,
        created_at: 1000,
        updated_at: 1002,
        duration_seconds: 1.5,
        results: [
          {
            filename: "img1.png",
            success: true,
            output_filename: "out_img1.png",
            error: null,
          },
          {
            filename: "img2.png",
            success: true,
            output_filename: "out_img2.png",
            error: null,
          },
        ],
      });

    await act(async () => {
      fireEvent.click(
        screen.getByRole("button", { name: /Process 2 Images/i }),
      );
    });
    expect(createBatchJob).toHaveBeenCalledWith(
      [file1, file2],
      mockGraph,
      "png",
    );

    // Flush: createBatchJob resolves → setJobId → useEffect → poll() → getBatchJobStatus resolves → setSummary
    await flushPromises();

    expect(screen.getByText("Processing Images...")).toBeDefined();
    expect(screen.getByText("1 / 2")).toBeDefined();

    // Trigger the 1-second setTimeout for the next poll
    await act(async () => {
      vi.advanceTimersByTime(1000);
    });
    // Flush: second poll() → getBatchJobStatus resolves "completed" → setSummary
    await flushPromises();

    expect(screen.getByText("Batch Run Completed Successfully")).toBeDefined();
    expect(screen.getByText("2 / 2")).toBeDefined();
    expect(screen.getByText("Output: out_img1.png")).toBeDefined();
    expect(screen.getByText("Output: out_img2.png")).toBeDefined();
  });

  // ── 5. Polling with partial failures ─────────────────────────────────────
  // Also uses fake timers; uses flushPromises instead of waitFor for same reason.
  it("handles failures during polling and displays them", async () => {
    vi.useFakeTimers();
    const { container } = renderModal();
    const fileInput = container.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await act(async () => {
      fireEvent.change(fileInput, {
        target: {
          files: [
            new File(["a"], "img1.png", { type: "image/png" }),
            new File(["b"], "img2.png", { type: "image/png" }),
          ],
        },
      });
    });

    vi.mocked(createBatchJob).mockResolvedValueOnce({
      job_id: "job-fail-123",
      status: "pending",
      total_files: 2,
    });
    vi.mocked(getBatchJobStatus).mockResolvedValueOnce({
      job_id: "job-fail-123",
      status: "completed",
      total_files: 2,
      processed_files: 2,
      success_count: 1,
      failure_count: 1,
      created_at: 1000,
      updated_at: 1002,
      duration_seconds: 1.2,
      results: [
        {
          filename: "img1.png",
          success: true,
          output_filename: "out_img1.png",
          error: null,
        },
        {
          filename: "img2.png",
          success: false,
          output_filename: null,
          error: "Internal processing crash",
        },
      ],
    });

    await act(async () => {
      fireEvent.click(
        screen.getByRole("button", { name: /Process 2 Images/i }),
      );
    });
    // Flush full async chain (first poll resolves to "completed" immediately)
    await flushPromises();

    expect(screen.getByText("Batch Run Completed with Failures")).toBeDefined();
    expect(screen.getByText("Internal processing crash")).toBeDefined();
  });

  // ── 6. Error on job creation ─────────────────────────────────────────────
  // No fake timers — waitFor works normally here.
  it("handles errors when batch job start fails", async () => {
    const { container } = renderModal();
    const fileInput = container.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await act(async () => {
      fireEvent.change(fileInput, {
        target: {
          files: [new File(["a"], "img1.png", { type: "image/png" })],
        },
      });
    });

    vi.mocked(createBatchJob).mockRejectedValueOnce(
      new Error("Unable to contact server"),
    );

    await act(async () => {
      fireEvent.click(
        screen.getByRole("button", { name: /Process 1 Images/i }),
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Error:")).toBeDefined();
      expect(screen.getByText(/Unable to contact server/)).toBeDefined();
    });
  });

  // ── 7. Error during polling ───────────────────────────────────────────────
  // Fake timers active; uses flushPromises instead of waitFor.
  it("handles errors during polling loop", async () => {
    vi.useFakeTimers();
    const { container } = renderModal();
    const fileInput = container.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await act(async () => {
      fireEvent.change(fileInput, {
        target: {
          files: [new File(["a"], "img1.png", { type: "image/png" })],
        },
      });
    });

    vi.mocked(createBatchJob).mockResolvedValueOnce({
      job_id: "job-poll-err",
      status: "pending",
      total_files: 1,
    });
    vi.mocked(getBatchJobStatus).mockRejectedValue(
      new Error("Network connection lost mid-polling"),
    );

    await act(async () => {
      fireEvent.click(
        screen.getByRole("button", { name: /Process 1 Images/i }),
      );
    });
    // Flush: createBatchJob resolves → setJobId → useEffect fires → poll() → getBatchJobStatus rejects → setError
    await flushPromises();

    expect(
      screen.getByText(/Network connection lost mid-polling/),
    ).toBeDefined();
  });

  // ── 8. Reset to initial state ─────────────────────────────────────────────
  // Uses fake timers to control polling
  it("resets component when 'New Batch' is clicked", async () => {
    vi.useFakeTimers();
    const { container } = renderModal();
    const fileInput = container.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await act(async () => {
      fireEvent.change(fileInput, {
        target: {
          files: [new File(["a"], "img1.png", { type: "image/png" })],
        },
      });
    });

    vi.mocked(createBatchJob).mockResolvedValueOnce({
      job_id: "job-reset",
      status: "pending",
      total_files: 1,
    });
    vi.mocked(getBatchJobStatus).mockResolvedValueOnce({
      job_id: "job-reset",
      status: "completed",
      total_files: 1,
      processed_files: 1,
      success_count: 1,
      failure_count: 0,
      created_at: 1000,
      updated_at: 1001,
      duration_seconds: 0.5,
      results: [
        {
          filename: "img1.png",
          success: true,
          output_filename: "out_img1.png",
          error: null,
        },
      ],
    });

    await act(async () => {
      fireEvent.click(
        screen.getByRole("button", { name: /Process 1 Images/i }),
      );
    });
    // Flush: createBatchJob resolves → setJobId → useEffect fires → poll() → getBatchJobStatus resolves "completed"
    await flushPromises();

    expect(
      screen.getByText("Batch Run Completed Successfully"),
    ).toBeDefined();

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /New Batch/i }));
    });

    expect(
      screen.getByText("Drag & drop your images here, or click to browse"),
    ).toBeDefined();
    expect(
      screen.queryByText("Batch Run Completed Successfully"),
    ).toBeNull();
  });

  // ── 9. ZIP download ───────────────────────────────────────────────────────
  // Uses fake timers to control polling
  it("triggers fetch download for ZIP when Download ZIP is clicked", async () => {
    vi.useFakeTimers();
    const { container } = renderModal();
    const fileInput = container.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await act(async () => {
      fireEvent.change(fileInput, {
        target: {
          files: [new File(["a"], "img1.png", { type: "image/png" })],
        },
      });
    });

    vi.mocked(createBatchJob).mockResolvedValueOnce({
      job_id: "job-zip-12345",
      status: "pending",
      total_files: 1,
    });
    vi.mocked(getBatchJobStatus).mockResolvedValueOnce({
      job_id: "job-zip-12345",
      status: "completed",
      total_files: 1,
      processed_files: 1,
      success_count: 1,
      failure_count: 0,
      created_at: 1000,
      updated_at: 1001,
      duration_seconds: 0.5,
      results: [
        {
          filename: "img1.png",
          success: true,
          output_filename: "out_img1.png",
          error: null,
        },
      ],
    });

    await act(async () => {
      fireEvent.click(
        screen.getByRole("button", { name: /Process 1 Images/i }),
      );
    });
    // Flush: createBatchJob resolves → setJobId → useEffect fires → poll() → getBatchJobStatus resolves "completed"
    await flushPromises();

    expect(
      screen.getByText("Batch Run Completed Successfully"),
    ).toBeDefined();

    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        blob: async () =>
          new Blob(["zip-content"], { type: "application/zip" }),
      } as Response);

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /Download ZIP/i }));
    });
    // Flush the fetch → blob → createObjectURL → click chain
    await flushPromises();

    expect(getBatchJobDownloadUrl).toHaveBeenCalledWith("job-zip-12345");
    expect(fetchSpy).toHaveBeenCalledWith(
      "http://localhost:4100/api/v1/batch-jobs/job-zip-12345/download",
    );
    expect(window.URL.createObjectURL).toHaveBeenCalled();
    expect(window.URL.revokeObjectURL).toHaveBeenCalled();

    fetchSpy.mockRestore();
  });
});
