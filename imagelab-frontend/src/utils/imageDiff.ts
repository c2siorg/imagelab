/**
 * Image Difference, Perceptual Delta & Pixel Heatmap Engine
 *
 * Provides client-side pixel comparison, Euclidean delta analysis, perceptual difference
 * heatmaps, and blend compositing between two images without requiring server round-trips.
 *
 * Mathematical Foundations:
 * 1. Pixel-wise Euclidean distance in RGB color space:
 *    d(p_A, p_B) = sqrt( (R_A - R_B)^2 + (G_A - G_B)^2 + (B_A - B_B)^2 )
 *    Normalized metric:
 *    delta_norm = d(p_A, p_B) / sqrt(3 * 255^2) in [0, 1]
 *
 * 2. Perceptual Luminance Difference (Rec. 601 Luma weighting):
 *    Y_A = 0.299 * R_A + 0.587 * G_A + 0.114 * B_A
 *    Y_B = 0.299 * R_B + 0.587 * G_B + 0.114 * B_B
 *    delta_Y = |Y_A - Y_B|
 *
 * 3. Statistical Metrics:
 *    - Mean Absolute Error (MAE): (1/N) * sum(|Y_A - Y_B|)
 *    - Root Mean Square Error (RMSE): sqrt( (1/N) * sum((Y_A - Y_B)^2) )
 *    - Altered Pixel Ratio: (N_changed / N_total) * 100%
 */

export type ColormapType = "thermal" | "grayscale" | "highlight" | "jet";

export interface PixelDiffOptions {
  /** Minimum pixel delta required to flag a change (0 to 255). Default 5. */
  toleranceThreshold?: number;
  /** Colormap used to visualize delta intensity. Default 'thermal'. */
  colormap?: ColormapType;
  /** Whether to emphasize alpha transparency discrepancies. Default false. */
  includeAlpha?: boolean;
  /** Sensitivity amplification multiplier (e.g. 1 to 20x). Default 1. */
  gain?: number;
}

export interface PixelDiffMetrics {
  /** Total pixels evaluated */
  totalPixels: number;
  /** Number of pixels exceeding tolerance threshold */
  alteredPixels: number;
  /** Percentage of pixels altered [0.0 - 100.0] */
  alteredPercentage: number;
  /** Mean Absolute Error across all pixels [0.0 - 255.0] */
  meanAbsoluteError: number;
  /** Root Mean Square Error [0.0 - 255.0] */
  rootMeanSquareError: number;
  /** Maximum pixel delta recorded [0 - 255] */
  peakDelta: number;
}

export interface DiffCalculationResult {
  metrics: PixelDiffMetrics;
  /** RGBA pixel buffer formatted for HTML5 ImageData */
  diffBuffer: Uint8ClampedArray;
}

/**
 * Maps a normalized scalar intensity [0.0, 1.0] to an RGBA color gradient.
 *
 * @param t - Normalized difference in range [0, 1]
 * @param colormap - Visual gradient styling
 * @returns [R, G, B, A] tuple in range 0-255
 */
export function mapNormalizedDiffToColor(
  t: number,
  colormap: ColormapType = "thermal",
): [number, number, number, number] {
  const clamped = Math.max(0, Math.min(1, t));

  switch (colormap) {
    case "grayscale": {
      const gray = Math.round(clamped * 255);
      return [gray, gray, gray, 255];
    }

    case "highlight": {
      // Unaltered pixels are faint translucent dark, altered pixels are vibrant neon green/cyan
      if (clamped < 0.02) {
        return [20, 24, 39, 140]; // Dark blueprint background
      }
      return [Math.round(20 + clamped * 80), Math.round(180 + clamped * 75), Math.round(240), 255];
    }

    case "jet": {
      // Classic Jet: Blue -> Cyan -> Yellow -> Orange -> Red
      const r = Math.max(0, Math.min(255, Math.round(255 * (1.5 - Math.abs(clamped * 4 - 3)))));
      const g = Math.max(0, Math.min(255, Math.round(255 * (1.5 - Math.abs(clamped * 4 - 2)))));
      const b = Math.max(0, Math.min(255, Math.round(255 * (1.5 - Math.abs(clamped * 4 - 1)))));
      return [r, g, b, 255];
    }

    case "thermal":
    default: {
      // High-contrast Inferno / Thermal: Deep Indigo (0) -> Magenta (0.35) -> Warm Orange (0.7) -> Bright Yellow (1.0)
      let r = 0;
      let g = 0;
      let b = 0;

      if (clamped < 0.33) {
        // Deep purple to magenta
        const factor = clamped / 0.33;
        r = Math.round(20 + factor * 160);
        g = Math.round(factor * 30);
        b = Math.round(70 + factor * 130);
      } else if (clamped < 0.66) {
        // Magenta to orange
        const factor = (clamped - 0.33) / 0.33;
        r = Math.round(180 + factor * 60);
        g = Math.round(30 + factor * 120);
        b = Math.round(200 * (1 - factor));
      } else {
        // Orange to electric yellow/white
        const factor = (clamped - 0.66) / 0.34;
        r = 240 + Math.round(factor * 15);
        g = Math.round(150 + factor * 105);
        b = Math.round(factor * 200);
      }
      return [r, g, b, 255];
    }
  }
}

/**
 * Computes pixel-by-pixel differences between two RGBA buffers of identical dimensions.
 *
 * @param bufferA - Primary (Before / Reference) RGBA pixel buffer
 * @param bufferB - Secondary (After / Modified) RGBA pixel buffer
 * @param width - Pixel width of buffers
 * @param height - Pixel height of buffers
 * @param options - Tolerance and colormap configuration
 * @returns Structured metrics and output diff image buffer
 */
export function computePixelDifference(
  bufferA: Uint8ClampedArray,
  bufferB: Uint8ClampedArray,
  width: number,
  height: number,
  options: PixelDiffOptions = {},
): DiffCalculationResult {
  const threshold = options.toleranceThreshold ?? 5;
  const colormap = options.colormap ?? "thermal";
  const includeAlpha = options.includeAlpha ?? false;
  const gain = Math.max(1, Math.min(20, options.gain ?? 1));

  const totalPixels = width * height;
  const diffBuffer = new Uint8ClampedArray(bufferA.length);

  let alteredPixels = 0;
  let absoluteErrorSum = 0;
  let squaredErrorSum = 0;
  let peakDelta = 0;

  // Max theoretical Euclidean RGB distance = sqrt(3 * 255^2) ≈ 441.67
  const maxDistance = Math.sqrt(3 * 255 * 255);

  for (let i = 0; i < totalPixels; i++) {
    const idx = i * 4;
    const rA = bufferA[idx];
    const gA = bufferA[idx + 1];
    const bA = bufferA[idx + 2];
    const aA = bufferA[idx + 3];

    const rB = bufferB[idx];
    const gB = bufferB[idx + 1];
    const bB = bufferB[idx + 2];
    const aB = bufferB[idx + 3];

    // Compute RGB Euclidean distance
    const dr = rA - rB;
    const dg = gA - gB;
    const db = bA - bB;
    const dist = Math.sqrt(dr * dr + dg * dg + db * db);

    let effectiveDelta = dist;
    if (includeAlpha) {
      const da = Math.abs(aA - aB);
      effectiveDelta = Math.max(dist, da);
    }

    if (effectiveDelta > peakDelta) {
      peakDelta = effectiveDelta;
    }

    // Perceptual Luma error calculation
    const lumaA = 0.299 * rA + 0.587 * gA + 0.114 * bA;
    const lumaB = 0.299 * rB + 0.587 * gB + 0.114 * bB;
    const lumaError = Math.abs(lumaA - lumaB);

    absoluteErrorSum += lumaError;
    squaredErrorSum += lumaError * lumaError;

    if (effectiveDelta > threshold) {
      alteredPixels++;
    }

    // Normalize delta [0, 1] for heatmap coloring with optional gain amplification
    const normalized = Math.min(1.0, (dist / maxDistance) * gain);
    const [outR, outG, outB, outA] = mapNormalizedDiffToColor(normalized, colormap);

    diffBuffer[idx] = outR;
    diffBuffer[idx + 1] = outG;
    diffBuffer[idx + 2] = outB;
    diffBuffer[idx + 3] = outA;
  }

  const alteredPercentage =
    totalPixels > 0 ? Number(((alteredPixels / totalPixels) * 100).toFixed(2)) : 0;
  const meanAbsoluteError =
    totalPixels > 0 ? Number((absoluteErrorSum / totalPixels).toFixed(2)) : 0;
  const rootMeanSquareError =
    totalPixels > 0 ? Number(Math.sqrt(squaredErrorSum / totalPixels).toFixed(2)) : 0;

  return {
    metrics: {
      totalPixels,
      alteredPixels,
      alteredPercentage,
      meanAbsoluteError,
      rootMeanSquareError,
      peakDelta: Math.round(peakDelta),
    },
    diffBuffer,
  };
}

/**
 * Generates an SVG or HTML5 canvas representing the difference heatmap.
 *
 * @param imgA - Before image bitmap
 * @param imgB - After image bitmap
 * @param targetCanvas - Canvas element to write into
 * @param options - Heatmap settings
 * @returns Computed metrics
 */
export function renderDiffToCanvas(
  imgA: HTMLImageElement | HTMLCanvasElement,
  imgB: HTMLImageElement | HTMLCanvasElement,
  targetCanvas: HTMLCanvasElement,
  options?: PixelDiffOptions,
): PixelDiffMetrics | null {
  const width = Math.min(imgA.width, imgB.width);
  const height = Math.min(imgA.height, imgB.height);

  if (width <= 0 || height <= 0) return null;

  targetCanvas.width = width;
  targetCanvas.height = height;

  const ctx = targetCanvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) return null;

  // Offscreen extraction
  const offCanvasA = document.createElement("canvas");
  offCanvasA.width = width;
  offCanvasA.height = height;
  const ctxA = offCanvasA.getContext("2d", { willReadFrequently: true });

  const offCanvasB = document.createElement("canvas");
  offCanvasB.width = width;
  offCanvasB.height = height;
  const ctxB = offCanvasB.getContext("2d", { willReadFrequently: true });

  if (!ctxA || !ctxB) return null;

  ctxA.drawImage(imgA, 0, 0, width, height);
  ctxB.drawImage(imgB, 0, 0, width, height);

  const dataA = ctxA.getImageData(0, 0, width, height).data;
  const dataB = ctxB.getImageData(0, 0, width, height).data;

  const { metrics, diffBuffer } = computePixelDifference(dataA, dataB, width, height, options);

  const outImageData = ctx.createImageData(width, height);
  outImageData.data.set(diffBuffer);
  ctx.putImageData(outImageData, 0, 0);

  return metrics;
}
