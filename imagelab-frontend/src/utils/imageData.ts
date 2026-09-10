export class BlobReadError extends Error {
  constructor(message: string, options?: { cause?: unknown }) {
    super(message, options);
    this.name = "BlobReadError";
  }
}

export function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = () => {
      if (typeof reader.result === "string") {
        resolve(reader.result);
        return;
      }

      reject(new BlobReadError("Blob read returned a non-string result."));
    };

    reader.onerror = () => {
      reject(new BlobReadError("Blob read failed.", { cause: reader.error }));
    };

    reader.readAsDataURL(blob);
  });
}

const SUPPORTED_IMAGE_FORMATS = new Set(["png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif"]);

export function getImageFormatFromMimeType(type: string | undefined): string {
  if (!type) return "png";

  const [, subtype = ""] = type.split("/");
  const format = subtype.toLowerCase();

  // Reject compound subtypes (e.g. "svg+xml") and unsupported formats like "gif"
  if (!format || !SUPPORTED_IMAGE_FORMATS.has(format)) return "png";

  return format;
}
