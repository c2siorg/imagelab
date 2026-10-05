import { afterEach, describe, expect, it, vi } from "vitest";
import { executePipeline, PipelineApiError } from "../../src/api/pipeline";
import type { PipelineRequest } from "../../src/types/pipeline";

const request: PipelineRequest = { image: "", image_format: "png", pipeline: [] };

function mockFetch(status: number, body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      json: () => (body instanceof Error ? Promise.reject(body) : Promise.resolve(body)),
    }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("executePipeline error handling", () => {
  it("surfaces the backend `error` message for a 400 validation response", async () => {
    const message =
      "Type mismatch on node 'abc' (imageconvertions_channelsplit), port 'None': expected channels in [3, 4], got 1 channels.";
    mockFetch(400, { success: false, execution_id: "", error: message, step: 0 });

    const promise = executePipeline(request);
    await expect(promise).rejects.toThrow(message);
    await expect(promise).rejects.not.toBeInstanceOf(PipelineApiError);
  });

  it("keeps PipelineApiError for a 400 body with step_type and message", async () => {
    mockFetch(400, {
      step_id: "b1",
      step_type: "blurring_applyblur",
      message: "Kernel size must be odd",
    });

    const promise = executePipeline(request);
    await expect(promise).rejects.toBeInstanceOf(PipelineApiError);
    await expect(promise).rejects.toMatchObject({
      detail: { step_type: "blurring_applyblur", message: "Kernel size must be odd" },
    });
  });

  it("falls back to a generic message when the 400 body is not JSON", async () => {
    mockFetch(400, new SyntaxError("Unexpected token"));

    await expect(executePipeline(request)).rejects.toThrow(
      "Pipeline execution failed with status 400",
    );
  });
});
