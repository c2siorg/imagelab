export class CanvasBlobError extends Error {
  constructor(message: string, options?: { cause?: unknown }) {
    super(message, options);
    this.name = "CanvasBlobError";
  }
}

export interface CanvasToBlobOptions {
  type?: string;
  quality?: number;
}

export type CanvasToBlobSource = Pick<HTMLCanvasElement, "toBlob">;

export function canvasToBlob(
  canvas: CanvasToBlobSource,
  options: CanvasToBlobOptions = {},
): Promise<Blob> {
  const { type, quality } = options;

  return new Promise<Blob>((resolve, reject) => {
    try {
      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob);
            return;
          }

          reject(new CanvasBlobError("Canvas conversion returned no blob."));
        },
        type,
        quality,
      );
    } catch (error) {
      reject(new CanvasBlobError("Canvas conversion failed.", { cause: error }));
    }
  });
}
