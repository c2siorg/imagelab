import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { executePipeline } from "../../src/api/pipeline";
import type { PipelineRequest } from "../../src/types/pipeline";

const MINIMAL_REQUEST: PipelineRequest = {
  image: "base64data",
  image_format: "png",
  pipeline: [{ type: "basic_readimage", params: {} }],
};

function mockResponse(status: number, body: unknown, ok = status >= 200 && status < 300): Response {
  return {
    ok,
    status,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response;
}

function mockResponseText(status: number, text: string): Response {
  return {
    ok: false,
    status,
    json: vi.fn().mockRejectedValue(new SyntaxError("Unexpected token")),
    text: vi.fn().mockResolvedValue(text),
  } as unknown as Response;
}

describe("executePipeline", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns parsed JSON on 200 OK", async () => {
    const payload = { success: true, image: "abc123", image_format: "png" };
    vi.mocked(fetch).mockResolvedValue(mockResponse(200, payload));

    const result = await executePipeline(MINIMAL_REQUEST);

    expect(result).toEqual(payload);
  });

  it("posts to the correct endpoint with JSON body", async () => {
    vi.mocked(fetch).mockResolvedValue(mockResponse(200, { success: true }));

    await executePipeline(MINIMAL_REQUEST);

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/pipeline/execute"),
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(MINIMAL_REQUEST),
      }),
    );
  });

  it("returns structured error with 'detail' from FastAPI 422 response", async () => {
    vi.mocked(fetch).mockResolvedValue(
      mockResponse(422, { detail: "Image decoding failed" }),
    );

    const result = await executePipeline(MINIMAL_REQUEST);

    expect(result).toEqual({ success: false, error: "Image decoding failed" });
  });

  it("returns structured error with 'message' field when 'detail' is absent", async () => {
    vi.mocked(fetch).mockResolvedValue(
      mockResponse(400, { message: "Bad request" }),
    );

    const result = await executePipeline(MINIMAL_REQUEST);

    expect(result).toEqual({ success: false, error: "Bad request" });
  });

  it("falls back to HTTP status string when error body is not JSON", async () => {
    vi.mocked(fetch).mockResolvedValue(mockResponseText(500, "<html>Internal Server Error</html>"));

    const result = await executePipeline(MINIMAL_REQUEST);

    expect(result).toEqual({ success: false, error: "HTTP 500" });
  });

  it("falls back to HTTP status string when error body has no 'detail' or 'message'", async () => {
    vi.mocked(fetch).mockResolvedValue(
      mockResponse(503, { code: "SERVICE_UNAVAILABLE" }),
    );

    const result = await executePipeline(MINIMAL_REQUEST);

    expect(result).toEqual({ success: false, error: "HTTP 503" });
  });

  it("returns structured error on 500 with FastAPI detail", async () => {
    vi.mocked(fetch).mockResolvedValue(
      mockResponse(500, { detail: "Internal pipeline error" }),
    );

    const result = await executePipeline(MINIMAL_REQUEST);

    expect(result).toEqual({ success: false, error: "Internal pipeline error" });
  });
});
