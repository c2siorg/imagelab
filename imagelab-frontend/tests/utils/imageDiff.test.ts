/**
 * @vitest-environment jsdom
 */

import { describe, expect, it } from "vitest";
import {
  computePixelDifference,
  mapNormalizedDiffToColor,
  type ColormapType,
} from "../../src/utils/imageDiff";

describe("imageDiff Utility Suite", () => {
  describe("mapNormalizedDiffToColor", () => {
    it("maps normalized zero delta to dark base color in thermal colormap", () => {
      const [r, g, b, a] = mapNormalizedDiffToColor(0.0, "thermal");
      expect(r).toBe(20);
      expect(g).toBe(0);
      expect(b).toBe(70);
      expect(a).toBe(255);
    });

    it("maps maximum normalized delta (1.0) to bright yellow/white in thermal colormap", () => {
      const [r, g, b, a] = mapNormalizedDiffToColor(1.0, "thermal");
      expect(r).toBeGreaterThanOrEqual(240);
      expect(g).toBeGreaterThanOrEqual(240);
      expect(b).toBeGreaterThanOrEqual(200);
      expect(a).toBe(255);
    });

    it("maps grayscale colormap to linear monochrome values", () => {
      expect(mapNormalizedDiffToColor(0.0, "grayscale")).toEqual([0, 0, 0, 255]);
      expect(mapNormalizedDiffToColor(0.5, "grayscale")).toEqual([128, 128, 128, 255]);
      expect(mapNormalizedDiffToColor(1.0, "grayscale")).toEqual([255, 255, 255, 255]);
    });

    it("highlights altered pixels with vibrant cyan/green while sub-threshold is dark", () => {
      const subThreshold = mapNormalizedDiffToColor(0.01, "highlight");
      expect(subThreshold[3]).toBe(140); // Faint background opacity

      const activeChange = mapNormalizedDiffToColor(0.5, "highlight");
      expect(activeChange[1]).toBeGreaterThanOrEqual(180);
      expect(activeChange[3]).toBe(255);
    });

    it("clamps out-of-range normalized values to [0, 1]", () => {
      const negative = mapNormalizedDiffToColor(-0.5, "grayscale");
      expect(negative).toEqual([0, 0, 0, 255]);

      const excessive = mapNormalizedDiffToColor(2.5, "grayscale");
      expect(excessive).toEqual([255, 255, 255, 255]);
    });

    it.each(["thermal", "jet", "grayscale", "highlight"] as ColormapType[])(
      "generates valid 8-bit RGBA channels for colormap: %s",
      (cmap) => {
        const [r, g, b, a] = mapNormalizedDiffToColor(0.42, cmap);
        expect(r).toBeGreaterThanOrEqual(0);
        expect(r).toBeLessThanOrEqual(255);
        expect(g).toBeGreaterThanOrEqual(0);
        expect(g).toBeLessThanOrEqual(255);
        expect(b).toBeGreaterThanOrEqual(0);
        expect(b).toBeLessThanOrEqual(255);
        expect(a).toBeGreaterThanOrEqual(0);
        expect(a).toBeLessThanOrEqual(255);
      },
    );
  });

  describe("computePixelDifference", () => {
    it("reports zero differences for identical buffers", () => {
      const width = 10;
      const height = 10;
      const totalBytes = width * height * 4;

      const bufferA = new Uint8ClampedArray(totalBytes);
      const bufferB = new Uint8ClampedArray(totalBytes);

      // Fill with identical solid color (120, 140, 160, 255)
      for (let i = 0; i < totalBytes; i += 4) {
        bufferA[i] = 120;
        bufferA[i + 1] = 140;
        bufferA[i + 2] = 160;
        bufferA[i + 3] = 255;

        bufferB[i] = 120;
        bufferB[i + 1] = 140;
        bufferB[i + 2] = 160;
        bufferB[i + 3] = 255;
      }

      const { metrics, diffBuffer } = computePixelDifference(bufferA, bufferB, width, height);

      expect(metrics.totalPixels).toBe(100);
      expect(metrics.alteredPixels).toBe(0);
      expect(metrics.alteredPercentage).toBe(0.0);
      expect(metrics.meanAbsoluteError).toBe(0.0);
      expect(metrics.rootMeanSquareError).toBe(0.0);
      expect(metrics.peakDelta).toBe(0);
      expect(diffBuffer.length).toBe(totalBytes);
    });

    it("accurately detects inverted pixels with high delta", () => {
      const width = 2;
      const height = 2;
      const totalBytes = width * height * 4;

      const bufferA = new Uint8ClampedArray(totalBytes); // All black (0, 0, 0, 255)
      const bufferB = new Uint8ClampedArray(totalBytes); // All white (255, 255, 255, 255)

      for (let i = 0; i < totalBytes; i += 4) {
        bufferA[i] = 0;
        bufferA[i + 1] = 0;
        bufferA[i + 2] = 0;
        bufferA[i + 3] = 255;

        bufferB[i] = 255;
        bufferB[i + 1] = 255;
        bufferB[i + 2] = 255;
        bufferB[i + 3] = 255;
      }

      const { metrics } = computePixelDifference(bufferA, bufferB, width, height);

      expect(metrics.totalPixels).toBe(4);
      expect(metrics.alteredPixels).toBe(4);
      expect(metrics.alteredPercentage).toBe(100.0);
      // Euclidean dist for (255,255,255) vs (0,0,0) is sqrt(3 * 255^2) ≈ 441.67 -> round to 442
      expect(metrics.peakDelta).toBe(442);
      expect(metrics.meanAbsoluteError).toBe(255.0);
      expect(metrics.rootMeanSquareError).toBe(255.0);
    });

    it("respects toleranceThreshold to filter out subtle compression noise", () => {
      const width = 2;
      const height = 2;
      const totalBytes = width * height * 4;

      const bufferA = new Uint8ClampedArray(totalBytes).fill(100);
      const bufferB = new Uint8ClampedArray(totalBytes).fill(100);

      // Pixel 0 has a subtle 3-level delta (sqrt(3^2 + 3^2 + 3^2) ≈ 5.19)
      bufferB[0] = 103;
      bufferB[1] = 103;
      bufferB[2] = 103;

      // With tolerance = 10, this subtle shift should not be counted as altered
      const resultStrict = computePixelDifference(bufferA, bufferB, width, height, {
        toleranceThreshold: 10,
      });
      expect(resultStrict.metrics.alteredPixels).toBe(0);

      // With tolerance = 2, it should be counted
      const resultSensitive = computePixelDifference(bufferA, bufferB, width, height, {
        toleranceThreshold: 2,
      });
      expect(resultSensitive.metrics.alteredPixels).toBe(1);
    });

    it("accurately handles alpha channel sensitivity when includeAlpha is enabled", () => {
      const width = 1;
      const height = 1;

      const bufferA = new Uint8ClampedArray([100, 100, 100, 255]);
      const bufferB = new Uint8ClampedArray([100, 100, 100, 50]); // Same RGB, transparent alpha

      // Without includeAlpha, RGB delta is 0
      const withoutAlpha = computePixelDifference(bufferA, bufferB, width, height, {
        includeAlpha: false,
      });
      expect(withoutAlpha.metrics.alteredPixels).toBe(0);

      // With includeAlpha, delta is detected
      const withAlpha = computePixelDifference(bufferA, bufferB, width, height, {
        includeAlpha: true,
      });
      expect(withAlpha.metrics.alteredPixels).toBe(1);
      expect(withAlpha.metrics.peakDelta).toBe(205); // 255 - 50 = 205
    });

    it("computes accurate Rec. 601 Luma perceptual error", () => {
      const width = 1;
      const height = 1;

      // Pure Green (0, 255, 0) has Luma = 0.587 * 255 ≈ 149.685
      const bufferA = new Uint8ClampedArray([0, 255, 0, 255]);
      // Pure Blue (0, 0, 255) has Luma = 0.114 * 255 ≈ 29.07
      const bufferB = new Uint8ClampedArray([0, 0, 255, 255]);

      const { metrics } = computePixelDifference(bufferA, bufferB, width, height);

      // Delta Luma ≈ |149.685 - 29.07| = 120.615 -> rounded to 120.62
      expect(metrics.meanAbsoluteError).toBeCloseTo(120.62, 1);
    });

    it("amplifies subtle differences when gain is specified", () => {
      const bufA = new Uint8ClampedArray([100, 100, 100, 255]);
      const bufB = new Uint8ClampedArray([110, 100, 100, 255]); // delta = 10
      const standard = computePixelDifference(bufA, bufB, 1, 1, {
        colormap: "grayscale",
        gain: 1,
      });
      const amplified = computePixelDifference(bufA, bufB, 1, 1, {
        colormap: "grayscale",
        gain: 5,
      });

      // Amplified diff buffer should produce a higher grayscale value than standard
      expect(amplified.diffBuffer[0]).toBeGreaterThan(standard.diffBuffer[0]);
    });
  });
});
