import { describe, expect, it } from "vitest";
import { CanvasBlobError, canvasToBlob } from "../../src/utils/canvas";

type CanvasLike = Pick<HTMLCanvasElement, "toBlob">;

describe("canvasToBlob", () => {
  it("resolves with the blob returned by canvas.toBlob", async () => {
    const blob = new Blob(["image"], { type: "image/png" });
    const canvas = {
      toBlob(callback, type, quality) {
        expect(type).toBe("image/png");
        expect(quality).toBe(0.8);
        callback(blob);
      },
    } satisfies CanvasLike;

    await expect(
      canvasToBlob(canvas, { type: "image/png", quality: 0.8 }),
    ).resolves.toBe(blob);
  });

  it("rejects when canvas.toBlob returns null", async () => {
    const canvas = {
      toBlob(callback) {
        callback(null);
      },
    } satisfies CanvasLike;

    await expect(canvasToBlob(canvas)).rejects.toMatchObject({
      name: "CanvasBlobError",
      message: "Canvas conversion returned no blob.",
    });
  });

  it("wraps synchronous canvas.toBlob failures in a CanvasBlobError", async () => {
    const rootCause = new Error("boom");
    const canvas = {
      toBlob() {
        throw rootCause;
      },
    } satisfies CanvasLike;

    await expect(canvasToBlob(canvas)).rejects.toMatchObject({
      name: "CanvasBlobError",
      message: "Canvas conversion failed.",
      cause: rootCause,
    });
  });

  it("exposes a dedicated error type for callers that want custom handling", () => {
    const error = new CanvasBlobError("Canvas conversion failed.");

    expect(error).toBeInstanceOf(Error);
    expect(error.name).toBe("CanvasBlobError");
  });
});
