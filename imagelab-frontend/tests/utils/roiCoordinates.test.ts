/**
 * @vitest-environment jsdom
 */

import { describe, expect, it } from "vitest";
import {
  applyAspectRatio,
  calculateRoiStatistics,
  clampRoiBox,
  imageToViewportCoordinates,
  normalizeBoundingBox,
  resizeBoundingBox,
  translateBoundingBox,
  viewportToImageCoordinates,
  type BoundingBox,
  type Dimensions,
  type Point,
} from "../../src/utils/roiCoordinates";

describe("roiCoordinates Utility Suite", () => {
  describe("normalizeBoundingBox", () => {
    it("normalizes canonical top-left to bottom-right coordinates", () => {
      const p1: Point = { x: 10, y: 20 };
      const p2: Point = { x: 100, y: 150 };
      const box = normalizeBoundingBox(p1, p2);

      expect(box).toEqual({ x1: 10, y1: 20, x2: 100, y2: 150 });
    });

    it("normalizes inverted drag coordinates (bottom-right to top-left)", () => {
      const p1: Point = { x: 100, y: 150 };
      const p2: Point = { x: 10, y: 20 };
      const box = normalizeBoundingBox(p1, p2);

      expect(box).toEqual({ x1: 10, y1: 20, x2: 100, y2: 150 });
    });

    it("normalizes cross-diagonal drag coordinates", () => {
      const p1: Point = { x: 10, y: 150 };
      const p2: Point = { x: 100, y: 20 };
      const box = normalizeBoundingBox(p1, p2);

      expect(box).toEqual({ x1: 10, y1: 20, x2: 100, y2: 150 });
    });

    it("handles zero-dimension points cleanly", () => {
      const p1: Point = { x: 50, y: 50 };
      const p2: Point = { x: 50, y: 50 };
      const box = normalizeBoundingBox(p1, p2);

      expect(box).toEqual({ x1: 50, y1: 50, x2: 50, y2: 50 });
    });
  });

  describe("viewportToImageCoordinates", () => {
    const displayDims: Dimensions = { width: 400, height: 300 };
    const naturalDims: Dimensions = { width: 800, height: 600 }; // 2x scale

    it("scales viewport coordinates to 2x natural dimensions", () => {
      const point = viewportToImageCoordinates({ x: 100, y: 50 }, displayDims, naturalDims);
      expect(point).toEqual({ x: 200, y: 100 });
    });

    it("clamps negative coordinates to zero", () => {
      const point = viewportToImageCoordinates({ x: -25, y: -50 }, displayDims, naturalDims);
      expect(point).toEqual({ x: 0, y: 0 });
    });

    it("clamps coordinates exceeding display boundaries to natural dimensions", () => {
      const point = viewportToImageCoordinates({ x: 500, y: 400 }, displayDims, naturalDims);
      expect(point).toEqual({ x: 800, y: 600 });
    });

    it("handles zero display dimensions gracefully without throwing", () => {
      const point = viewportToImageCoordinates(
        { x: 100, y: 50 },
        { width: 0, height: 0 },
        naturalDims,
      );
      expect(point).toEqual({ x: 0, y: 0 });
    });
  });

  describe("imageToViewportCoordinates", () => {
    const displayDims: Dimensions = { width: 400, height: 300 };
    const naturalDims: Dimensions = { width: 800, height: 600 }; // 0.5x scale

    it("projects natural image coordinates down to viewport CSS pixels", () => {
      const point = imageToViewportCoordinates({ x: 200, y: 100 }, displayDims, naturalDims);
      expect(point).toEqual({ x: 100, y: 50 });
    });

    it("handles zero natural dimensions safely", () => {
      const point = imageToViewportCoordinates({ x: 100, y: 50 }, displayDims, {
        width: 0,
        height: 0,
      });
      expect(point).toEqual({ x: 0, y: 0 });
    });
  });

  describe("clampRoiBox", () => {
    const bounds: Dimensions = { width: 640, height: 480 };

    it("keeps boxes within image boundaries unchanged", () => {
      const box: BoundingBox = { x1: 50, y1: 50, x2: 200, y2: 200 };
      expect(clampRoiBox(box, bounds)).toEqual(box);
    });

    it("clamps coordinates that spill beyond the right and bottom edges", () => {
      const box: BoundingBox = { x1: 500, y1: 400, x2: 700, y2: 550 };
      expect(clampRoiBox(box, bounds)).toEqual({ x1: 500, y1: 400, x2: 640, y2: 480 });
    });

    it("clamps negative coordinates to zero", () => {
      const box: BoundingBox = { x1: -50, y1: -30, x2: 150, y2: 120 };
      expect(clampRoiBox(box, bounds)).toEqual({ x1: 0, y1: 0, x2: 150, y2: 120 });
    });
  });

  describe("resizeBoundingBox", () => {
    const bounds: Dimensions = { width: 1000, height: 800 };
    const initialBox: BoundingBox = { x1: 100, y1: 100, x2: 300, y2: 300 };

    it("resizes via southeast (se) handle expanding width and height", () => {
      const currentPoint: Point = { x: 350, y: 380 };
      const resized = resizeBoundingBox(initialBox, "se", currentPoint, bounds);

      expect(resized).toEqual({ x1: 100, y1: 100, x2: 350, y2: 380 });
    });

    it("resizes via northwest (nw) handle adjusting top-left origin", () => {
      const currentPoint: Point = { x: 50, y: 80 };
      const resized = resizeBoundingBox(initialBox, "nw", currentPoint, bounds);

      expect(resized).toEqual({ x1: 50, y1: 80, x2: 300, y2: 300 });
    });

    it("resizes via north (n) handle affecting only vertical height", () => {
      const currentPoint: Point = { x: 200, y: 40 };
      const resized = resizeBoundingBox(initialBox, "n", currentPoint, bounds);

      expect(resized).toEqual({ x1: 100, y1: 40, x2: 300, y2: 300 });
    });

    it("resizes via east (e) handle affecting only horizontal width", () => {
      const currentPoint: Point = { x: 420, y: 200 };
      const resized = resizeBoundingBox(initialBox, "e", currentPoint, bounds);

      expect(resized).toEqual({ x1: 100, y1: 100, x2: 420, y2: 300 });
    });

    it("enforces minimum size threshold preventing handle inversion", () => {
      const currentPoint: Point = { x: 500, y: 500 }; // NW dragging past SE
      const resized = resizeBoundingBox(initialBox, "nw", currentPoint, bounds, 10);

      expect(resized.x1).toBeLessThanOrEqual(resized.x2 - 10);
      expect(resized.y1).toBeLessThanOrEqual(resized.y2 - 10);
    });
  });

  describe("applyAspectRatio", () => {
    it("locks box to 1:1 square ratio", () => {
      const box: BoundingBox = { x1: 0, y1: 0, x2: 200, y2: 100 }; // 2:1
      const squared = applyAspectRatio(box, 1.0);

      const width = squared.x2 - squared.x1;
      const height = squared.y2 - squared.y1;
      expect(width).toBe(height);
    });

    it("locks box to 16:9 widescreen ratio", () => {
      const box: BoundingBox = { x1: 0, y1: 0, x2: 320, y2: 240 }; // 4:3
      const widescreen = applyAspectRatio(box, 16 / 9);

      const width = widescreen.x2 - widescreen.x1;
      const height = widescreen.y2 - widescreen.y1;
      expect(width / height).toBeCloseTo(16 / 9, 1);
    });

    it("preserves center anchor point when center mode is specified", () => {
      const box: BoundingBox = { x1: 100, y1: 100, x2: 300, y2: 200 };
      const centerX = (box.x1 + box.x2) / 2;
      const centerY = (box.y1 + box.y2) / 2;

      const result = applyAspectRatio(box, 1.0, "center");
      const resultCenterX = (result.x1 + result.x2) / 2;
      const resultCenterY = (result.y1 + result.y2) / 2;

      expect(resultCenterX).toBeCloseTo(centerX, 0);
      expect(resultCenterY).toBeCloseTo(centerY, 0);
    });

    it("preserves southeast (se) anchor adjusting origin correctly", () => {
      const box: BoundingBox = { x1: 50, y1: 50, x2: 200, y2: 200 };
      const result = applyAspectRatio(box, 2.0, "se");

      expect(result.x2).toBe(200);
      expect(result.y2).toBe(200);
      expect((result.x2 - result.x1) / (result.y2 - result.y1)).toBeCloseTo(2.0, 1);
    });
  });

  describe("translateBoundingBox", () => {
    const bounds: Dimensions = { width: 800, height: 600 };
    const box: BoundingBox = { x1: 100, y1: 100, x2: 300, y2: 250 }; // 200x150

    it("translates box by positive offsets", () => {
      const moved = translateBoundingBox(box, { x: 50, y: 70 }, bounds);
      expect(moved).toEqual({ x1: 150, y1: 170, x2: 350, y2: 320 });
    });

    it("prevents translation past left and top edges", () => {
      const moved = translateBoundingBox(box, { x: -200, y: -300 }, bounds);
      expect(moved.x1).toBe(0);
      expect(moved.y1).toBe(0);
      expect(moved.x2).toBe(200);
      expect(moved.y2).toBe(150);
    });

    it("prevents translation past right and bottom boundaries", () => {
      const moved = translateBoundingBox(box, { x: 1000, y: 1000 }, bounds);
      expect(moved.x2).toBe(800);
      expect(moved.y2).toBe(600);
      expect(moved.x1).toBe(600); // 800 - 200
      expect(moved.y1).toBe(450); // 600 - 150
    });
  });

  describe("calculateRoiStatistics", () => {
    it("computes accurate area, aspect ratio and coverage percentage", () => {
      const box: BoundingBox = { x1: 0, y1: 0, x2: 400, y2: 300 };
      const totalDims: Dimensions = { width: 800, height: 600 };

      const stats = calculateRoiStatistics(box, totalDims);

      expect(stats.width).toBe(400);
      expect(stats.height).toBe(300);
      expect(stats.areaPixels).toBe(120000);
      expect(stats.aspectRatio).toBe(1.333);
      expect(stats.coveragePercentage).toBe(25.0); // 120,000 / 480,000 = 25%
    });

    it("handles edge cases with zero height or width safely", () => {
      const box: BoundingBox = { x1: 10, y1: 10, x2: 10, y2: 10 };
      const stats = calculateRoiStatistics(box);

      expect(stats.width).toBe(0);
      expect(stats.height).toBe(0);
      expect(stats.areaPixels).toBe(0);
      expect(stats.aspectRatio).toBe(0);
      expect(stats.coveragePercentage).toBe(0);
    });
  });
});
