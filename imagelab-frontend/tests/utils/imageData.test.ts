// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from "vitest";
import { BlobReadError, blobToDataUrl, getImageFormatFromMimeType } from "../../src/utils/imageData";

function createFileReaderEvent(type: string): ProgressEvent<FileReader> {
  return new ProgressEvent(type) as ProgressEvent<FileReader>;
}

class MockFileReader {
  static mode: "success" | "nonstr" | "error" = "success";

  public result: string | ArrayBuffer | null = null;
  public error: DOMException | null = null;
  public onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => unknown) | null = null;
  public onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => unknown) | null = null;

  readAsDataURL(blob: Blob) {
    void blob;

    if (MockFileReader.mode === "success") {
      this.result = "data:image/png;base64,ZmFrZQ==";
      this.onload?.call(this as unknown as FileReader, createFileReaderEvent("load"));
      return;
    }

    if (MockFileReader.mode === "nonstr") {
      this.result = new ArrayBuffer(8);
      this.onload?.call(this as unknown as FileReader, createFileReaderEvent("load"));
      return;
    }

    this.error = new DOMException("Read failed");
    this.onerror?.call(this as unknown as FileReader, createFileReaderEvent("error"));
  }
}

describe("blobToDataUrl", () => {
  const originalFileReader = globalThis.FileReader;

  afterEach(() => {
    MockFileReader.mode = "success";
    vi.unstubAllGlobals();
  });

  it("resolves the data URL returned by FileReader", async () => {
    vi.stubGlobal("FileReader", MockFileReader);

    await expect(blobToDataUrl(new Blob(["test"]))).resolves.toBe("data:image/png;base64,ZmFrZQ==");
  });

  it("rejects when FileReader returns a non-string result", async () => {
    MockFileReader.mode = "nonstr";
    vi.stubGlobal("FileReader", MockFileReader);

    await expect(blobToDataUrl(new Blob(["test"]))).rejects.toMatchObject({
      name: "BlobReadError",
      message: "Blob read returned a non-string result.",
    });
  });

  it("wraps FileReader failures in a BlobReadError", async () => {
    MockFileReader.mode = "error";
    vi.stubGlobal("FileReader", MockFileReader);

    await expect(blobToDataUrl(new Blob(["test"]))).rejects.toMatchObject({
      name: "BlobReadError",
      message: "Blob read failed.",
    });
  });

  it("exposes a dedicated error type", () => {
    const error = new BlobReadError("Blob read failed.");

    expect(error).toBeInstanceOf(Error);
    expect(error.name).toBe("BlobReadError");
  });

  it("restores the original FileReader after the test run", () => {
    expect(originalFileReader).toBeTypeOf("function");
  });
});

describe("getImageFormatFromMimeType", () => {
  it("extracts the subtype from an image mime type", () => {
    expect(getImageFormatFromMimeType("image/jpeg")).toBe("jpeg");
  });

  it("falls back to png when the mime type is missing", () => {
    expect(getImageFormatFromMimeType(undefined)).toBe("png");
  });
});
