import { describe, expect, it } from "vitest";
import {
  calculateLuma,
  calculateRoiMeasurements,
  getPixelNeighborhood,
  probePixel,
  rgbToHex,
} from "../../src/utils/pixelInspector";
import type { BoundingBox } from "../../src/utils/roiCoordinates";

function createMockImageData(
  width: number,
  height: number,
  fillFn: (x: number, y: number) => [number, number, number, number],
): ImageData {
  const data = new Uint8ClampedArray(width * height * 4);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4;
      const [r, g, b, a] = fillFn(x, y);
      data[idx] = r;
      data[idx + 1] = g;
      data[idx + 2] = b;
      data[idx + 3] = a;
    }
  }
  return {
    width,
    height,
    data,
    colorSpace: "srgb",
  } as ImageData;
}

describe("pixelInspector utility", () => {
  describe("rgbToHex", () => {
    it("converts black to #000000", () => {
      expect(rgbToHex(0, 0, 0)).toBe("#000000");
    });

    it("converts white to #FFFFFF", () => {
      expect(rgbToHex(255, 255, 255)).toBe("#FFFFFF");
    });

    it("converts pure red to #FF0000", () => {
      expect(rgbToHex(255, 0, 0)).toBe("#FF0000");
    });

    it("clamps out-of-range values", () => {
      expect(rgbToHex(-10, 300, 128)).toBe("#00FF80");
    });
  });

  describe("calculateLuma", () => {
    it("calculates ITU-R BT.601 weighted luminance correctly", () => {
      // White: 0.299*255 + 0.587*255 + 0.114*255 = 255
      expect(Math.round(calculateLuma(255, 255, 255))).toBe(255);
      // Pure Green: 0.587 * 255 = ~149.685
      expect(Math.round(calculateLuma(0, 255, 0))).toBe(150);
    });
  });

  describe("probePixel", () => {
    it("returns correct pixel probe at valid coordinates", () => {
      const imgData = createMockImageData(4, 4, (x, y) => [x * 50, y * 50, 100, 255]);
      const probe = probePixel(imgData, 2, 1);
      expect(probe).not.toBeNull();
      expect(probe?.x).toBe(2);
      expect(probe?.y).toBe(1);
      expect(probe?.r).toBe(100);
      expect(probe?.g).toBe(50);
      expect(probe?.b).toBe(100);
      expect(probe?.hex).toBe("#643264");
    });

    it("returns null for out-of-bounds coordinates", () => {
      const imgData = createMockImageData(4, 4, () => [255, 255, 255, 255]);
      expect(probePixel(imgData, -1, 0)).toBeNull();
      expect(probePixel(imgData, 4, 2)).toBeNull();
      expect(probePixel(imgData, 2, 5)).toBeNull();
    });
  });

  describe("getPixelNeighborhood", () => {
    it("extracts a 5x5 matrix centered at cursor (radius=2)", () => {
      const imgData = createMockImageData(10, 10, (x, y) => [x, y, 0, 255]);
      const matrix = getPixelNeighborhood(imgData, 5, 5, 2);

      expect(matrix.length).toBe(5);
      expect(matrix[0].length).toBe(5);

      // Center pixel (index 2, 2)
      expect(matrix[2][2]?.x).toBe(5);
      expect(matrix[2][2]?.y).toBe(5);

      // Top-left neighbor (index 0, 0) -> (3, 3)
      expect(matrix[0][0]?.x).toBe(3);
      expect(matrix[0][0]?.y).toBe(3);
    });

    it("handles boundary edges with null entries for out-of-bounds pixels", () => {
      const imgData = createMockImageData(5, 5, () => [128, 128, 128, 255]);
      // Top-left corner (0, 0)
      const matrix = getPixelNeighborhood(imgData, 0, 0, 1);
      expect(matrix.length).toBe(3);
      expect(matrix[0][0]).toBeNull(); // (-1, -1)
      expect(matrix[1][1]?.x).toBe(0); // center (0, 0)
      expect(matrix[2][2]?.x).toBe(1); // (1, 1)
    });
  });

  describe("calculateRoiMeasurements", () => {
    it("computes accurate ImageJ-style measurements on uniform region", () => {
      const imgData = createMockImageData(10, 10, () => [100, 100, 100, 255]);
      const box: BoundingBox = { x1: 2, y1: 2, x2: 6, y2: 6 }; // 4x4 = 16 pixels
      const metrics = calculateRoiMeasurements(imgData, box);

      expect(metrics).not.toBeNull();
      expect(metrics?.width).toBe(4);
      expect(metrics?.height).toBe(4);
      expect(metrics?.pixelCount).toBe(16);
      expect(metrics?.meanIntensity).toBe(100);
      expect(metrics?.minIntensity).toBe(100);
      expect(metrics?.maxIntensity).toBe(100);
      expect(metrics?.stdDev).toBe(0);
      expect(metrics?.histogram[100]).toBe(16);
    });

    it("computes variance and min/max on gradient region", () => {
      // 2x2 box with values 0 and 200
      const imgData = createMockImageData(2, 2, (x) => [x * 200, x * 200, x * 200, 255]);
      const box: BoundingBox = { x1: 0, y1: 0, x2: 2, y2: 2 };
      const metrics = calculateRoiMeasurements(imgData, box);

      expect(metrics).not.toBeNull();
      expect(metrics?.pixelCount).toBe(4);
      expect(metrics?.minIntensity).toBe(0);
      expect(metrics?.maxIntensity).toBe(200);
      expect(metrics?.meanIntensity).toBe(100);
      expect(metrics?.stdDev).toBeGreaterThan(0);
    });
  });
});
