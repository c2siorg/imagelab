/**
 * Pixel Inspector & Quantitative ROI Measurement Engine
 *
 * Modeled after ImageJ / Fiji's Pixel Inspection Tool and ROI Measure Analyzer.
 * Enables real-time sub-pixel probing, local neighborhood matrix extraction,
 * and statistical quantification of regions of interest (Mean, StdDev, Min, Max, Local Histogram).
 *
 * Mathematical Foundations:
 * 1. Pixel Sampling:
 *    Linear index for coordinate (x, y) in a row-major 4-channel RGBA buffer:
 *      index = (y * width + x) * 4
 *
 * 2. Perceptual Luminance (ITU-R BT.601 / Rec. 601 Luma):
 *      Y = 0.299 * R + 0.587 * G + 0.114 * B
 *
 * 3. Neighborhood Matrix (ImageJ Pixel Inspection Grid):
 *      Given cursor (c_x, c_y) and radius r (e.g. r=2 for a 5x5 window):
 *      grid[dy][dx] for dx, dy in [-r, r]
 *
 * 4. Sample Standard Deviation:
 *      s = sqrt( (1 / (N - 1)) * sum_{i=1}^N (Y_i - mu)^2 )  where mu = (1/N) * sum Y_i
 */

import type { BoundingBox } from "./roiCoordinates";

export interface PixelProbe {
  x: number;
  y: number;
  r: number;
  g: number;
  b: number;
  a: number;
  hex: string;
  luma: number;
  normalizedLuma: number;
}

export interface RoiMeasurements {
  width: number;
  height: number;
  pixelCount: number;
  meanIntensity: number;
  stdDev: number;
  minIntensity: number;
  maxIntensity: number;
  meanRgb: [number, number, number];
  histogram: number[]; // 256 intensity bins
}

/**
 * Converts standard RGB integer components into a uppercase hexadecimal color string (#RRGGBB).
 */
export function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (n: number) =>
    Math.max(0, Math.min(255, Math.round(n)))
      .toString(16)
      .padStart(2, "0")
      .toUpperCase();
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

/**
 * Computes ITU-R BT.601 perceptual luminance from RGB channels.
 */
export function calculateLuma(r: number, g: number, b: number): number {
  return 0.299 * r + 0.587 * g + 0.114 * b;
}

/**
 * Probes the exact pixel at (x, y) in natural raster coordinates from an ImageData buffer.
 *
 * @param imageData - Raw canvas pixel data
 * @param x - Intrinsic integer X coordinate
 * @param y - Intrinsic integer Y coordinate
 * @returns Pixel probe object with RGB, Luma, and Hex representation, or null if out of bounds
 */
export function probePixel(imageData: ImageData, x: number, y: number): PixelProbe | null {
  const px = Math.floor(x);
  const py = Math.floor(y);

  if (px < 0 || px >= imageData.width || py < 0 || py >= imageData.height) {
    return null;
  }

  const offset = (py * imageData.width + px) * 4;
  const data = imageData.data;

  const r = data[offset];
  const g = data[offset + 1];
  const b = data[offset + 2];
  const a = data[offset + 3];

  const luma = Number(calculateLuma(r, g, b).toFixed(1));
  const hex = rgbToHex(r, g, b);
  const normalizedLuma = Number((luma / 255).toFixed(3));

  return {
    x: px,
    y: py,
    r,
    g,
    b,
    a,
    hex,
    luma,
    normalizedLuma,
  };
}

/**
 * Extracts an (2*radius + 1) by (2*radius + 1) matrix of neighboring pixels centered at (cx, cy).
 * Mirrors ImageJ's 3x3 and 5x5 Pixel Inspection grid.
 *
 * @param imageData - Canvas ImageData
 * @param cx - Center X coordinate
 * @param cy - Center Y coordinate
 * @param radius - Half-width of neighborhood window (default 2 -> 5x5 grid)
 */
export function getPixelNeighborhood(
  imageData: ImageData,
  cx: number,
  cy: number,
  radius = 2,
): (PixelProbe | null)[][] {
  const size = radius * 2 + 1;
  const matrix: (PixelProbe | null)[][] = Array.from({ length: size }, () =>
    Array.from({ length: size }, () => null),
  );

  const startX = cx - radius;
  const startY = cy - radius;

  for (let row = 0; row < size; row++) {
    for (let col = 0; col < size; col++) {
      const sampleX = startX + col;
      const sampleY = startY + row;
      matrix[row][col] = probePixel(imageData, sampleX, sampleY);
    }
  }

  return matrix;
}

/**
 * Calculates quantitative intensity metrics (Mean, StdDev, Min, Max, Histogram)
 * for a Region of Interest directly from an ImageData buffer.
 *
 * @param imageData - Canvas raster buffer
 * @param box - Bounding box in raster pixel coordinates
 */
export function calculateRoiMeasurements(
  imageData: ImageData,
  box: BoundingBox,
): RoiMeasurements | null {
  const x1 = Math.max(0, Math.min(imageData.width - 1, Math.floor(Math.min(box.x1, box.x2))));
  const y1 = Math.max(0, Math.min(imageData.height - 1, Math.floor(Math.min(box.y1, box.y2))));
  const x2 = Math.max(0, Math.min(imageData.width, Math.ceil(Math.max(box.x1, box.x2))));
  const y2 = Math.max(0, Math.min(imageData.height, Math.ceil(Math.max(box.y1, box.y2))));

  const roiWidth = x2 - x1;
  const roiHeight = y2 - y1;
  const pixelCount = roiWidth * roiHeight;

  if (pixelCount <= 0) return null;

  const data = imageData.data;
  const imgWidth = imageData.width;

  let sumLuma = 0;
  let sumSqLuma = 0;
  let sumR = 0;
  let sumG = 0;
  let sumB = 0;
  let minIntensity = 255;
  let maxIntensity = 0;

  const histogram = new Array<number>(256).fill(0);

  for (let y = y1; y < y2; y++) {
    const rowOffset = y * imgWidth * 4;
    for (let x = x1; x < x2; x++) {
      const idx = rowOffset + x * 4;
      const r = data[idx];
      const g = data[idx + 1];
      const b = data[idx + 2];

      const luma = calculateLuma(r, g, b);
      const intLuma = Math.max(0, Math.min(255, Math.round(luma)));

      sumLuma += luma;
      sumSqLuma += luma * luma;
      sumR += r;
      sumG += g;
      sumB += b;

      if (intLuma < minIntensity) minIntensity = intLuma;
      if (intLuma > maxIntensity) maxIntensity = intLuma;

      histogram[intLuma]++;
    }
  }

  const meanIntensity = Number((sumLuma / pixelCount).toFixed(2));
  const variance =
    pixelCount > 1
      ? Math.max(0, (sumSqLuma - (sumLuma * sumLuma) / pixelCount) / (pixelCount - 1))
      : 0;
  const stdDev = Number(Math.sqrt(variance).toFixed(2));

  const meanRgb: [number, number, number] = [
    Math.round(sumR / pixelCount),
    Math.round(sumG / pixelCount),
    Math.round(sumB / pixelCount),
  ];

  return {
    width: roiWidth,
    height: roiHeight,
    pixelCount,
    meanIntensity,
    stdDev,
    minIntensity,
    maxIntensity,
    meanRgb,
    histogram,
  };
}

/**
 * Extracts an ImageData snapshot from an HTMLImageElement using an offscreen canvas.
 */
export function extractImageDataFromImageElement(img: HTMLImageElement): ImageData | null {
  if (!img.naturalWidth || !img.naturalHeight) return null;

  try {
    const canvas = document.createElement("canvas");
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return null;

    ctx.drawImage(img, 0, 0);
    return ctx.getImageData(0, 0, img.naturalWidth, img.naturalHeight);
  } catch {
    return null;
  }
}
