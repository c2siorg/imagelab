import { afterEach, describe, expect, it, vi } from "vitest";
import { exportPipelineAsPython } from "../src/api/pipeline";

const originalFetch = globalThis.fetch;

describe("exportPipelineAsPython", () => {
  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("returns script text when the API succeeds", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response("print('hello')", {
        status: 200,
        headers: { "Content-Type": "text/plain" },
      }),
    ) as typeof fetch;

    const result = await exportPipelineAsPython({
      pipeline: [{ type: "imageconvertions_grayimage", params: {} }],
    });

    expect(result).toBe("print('hello')");
  });

  it("throws the API detail when the export fails", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Unknown operator 'bad' at step 1" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }),
    ) as typeof fetch;

    await expect(
      exportPipelineAsPython({
        pipeline: [{ type: "bad", params: {} }],
      }),
    ).rejects.toThrow("Unknown operator 'bad' at step 1");
  });
});
