/**
 * ROI (Region of Interest) Coordinate Transformation & Geometry Utilities
 *
 * Provides bidirectional coordinate mapping between the screen display viewport (CSS pixels)
 * and intrinsic raster pixel dimensions (natural image coordinates), as well as constraint
 * solvers for aspect-ratio locking, 8-handle directional resizing, and bounding-box clamping.
 *
 * Mathematical Foundations:
 * Given a rendered image element with bounding client rect R_disp = (W_disp, H_disp)
 * and underlying natural raster dimensions R_nat = (W_nat, H_nat):
 *
 * Scale factors:
 *   s_x = W_nat / W_disp
 *   s_y = H_nat / H_disp
 *
 * Affine viewport-to-image projection:
 *   [ x_img ]   [ s_x   0   ] [ x_disp ]
 *   [ y_img ] = [  0   s_y  ] [ y_disp ]
 *
 * Subject to clamping constraints:
 *   x_img in [0, W_nat],  y_img in [0, H_nat]
 */

export interface Point {
  x: number;
  y: number;
}

export interface Dimensions {
  width: number;
  height: number;
}

export interface BoundingBox {
  /** Top-left X coordinate in pixel space */
  x1: number;
  /** Top-left Y coordinate in pixel space */
  y1: number;
  /** Bottom-right X coordinate in pixel space */
  x2: number;
  /** Bottom-right Y coordinate in pixel space */
  y2: number;
}

export interface RoiStatistics {
  width: number;
  height: number;
  areaPixels: number;
  aspectRatio: number;
  coveragePercentage: number;
}

export type ResizeHandle = "nw" | "n" | "ne" | "e" | "se" | "s" | "sw" | "w";

/**
 * Normalizes two arbitrary corner points into a canonical bounding box
 * where (x1, y1) is strictly top-left and (x2, y2) is strictly bottom-right.
 *
 * @param p1 - First corner point (e.g. pointerdown anchor)
 * @param p2 - Second corner point (e.g. current pointer position)
 * @returns Canonical bounding box with x1 <= x2 and y1 <= y2
 */
export function normalizeBoundingBox(p1: Point, p2: Point): BoundingBox {
  return {
    x1: Math.round(Math.min(p1.x, p2.x)),
    y1: Math.round(Math.min(p1.y, p2.y)),
    x2: Math.round(Math.max(p1.x, p2.x)),
    y2: Math.round(Math.max(p1.y, p2.y)),
  };
}

/**
 * Transforms a viewport coordinate (relative to the image element's top-left)
 * into intrinsic image pixel coordinates.
 *
 * @param viewportPoint - Point in CSS pixels relative to image element
 * @param displayDims - Rendered client width and height of the image element
 * @param naturalDims - Intrinsic natural width and height of the bitmap image
 * @returns Scaled and clamped coordinate in natural image pixel space
 */
export function viewportToImageCoordinates(
  viewportPoint: Point,
  displayDims: Dimensions,
  naturalDims: Dimensions,
): Point {
  if (displayDims.width <= 0 || displayDims.height <= 0) {
    return { x: 0, y: 0 };
  }

  const scaleX = naturalDims.width / displayDims.width;
  const scaleY = naturalDims.height / displayDims.height;

  const rawX = viewportPoint.x * scaleX;
  const rawY = viewportPoint.y * scaleY;

  return {
    x: Math.round(Math.max(0, Math.min(rawX, naturalDims.width))),
    y: Math.round(Math.max(0, Math.min(rawY, naturalDims.height))),
  };
}

/**
 * Transforms an intrinsic image coordinate into viewport coordinate space
 * for rendering overlays, guides, and handles over the image.
 *
 * @param imagePoint - Point in intrinsic raster image pixel space
 * @param displayDims - Rendered client width and height of the image element
 * @param naturalDims - Intrinsic natural width and height of the bitmap image
 * @returns Projected point in CSS display pixels
 */
export function imageToViewportCoordinates(
  imagePoint: Point,
  displayDims: Dimensions,
  naturalDims: Dimensions,
): Point {
  if (naturalDims.width <= 0 || naturalDims.height <= 0) {
    return { x: 0, y: 0 };
  }

  const scaleX = displayDims.width / naturalDims.width;
  const scaleY = displayDims.height / naturalDims.height;

  return {
    x: imagePoint.x * scaleX,
    y: imagePoint.y * scaleY,
  };
}

/**
 * Clamps a bounding box so all vertices strictly reside within the image dimensions.
 *
 * @param box - Unclamped bounding box
 * @param bounds - Max boundaries (width, height)
 * @returns Bounding box clamped strictly to [0, bounds.width] and [0, bounds.height]
 */
export function clampRoiBox(box: BoundingBox, bounds: Dimensions): BoundingBox {
  const x1 = Math.max(0, Math.min(box.x1, bounds.width));
  const y1 = Math.max(0, Math.min(box.y1, bounds.height));
  const x2 = Math.max(0, Math.min(box.x2, bounds.width));
  const y2 = Math.max(0, Math.min(box.y2, bounds.height));

  return {
    x1: Math.min(x1, x2),
    y1: Math.min(y1, y2),
    x2: Math.max(x1, x2),
    y2: Math.max(y1, y2),
  };
}

/**
 * Applies directional resizing to a bounding box based on the active handle being dragged.
 * Supports 8 compass directions with boundary enforcement and inversion prevention.
 *
 * @param initialBox - Starting bounding box when drag began
 * @param handle - Compass handle direction being dragged
 * @param currentPoint - Current pointer position in image pixel coordinates
 * @param bounds - Natural image boundaries for clamping
 * @param minSize - Minimum allowed box width and height in pixels
 * @returns Updated bounding box
 */
export function resizeBoundingBox(
  initialBox: BoundingBox,
  handle: ResizeHandle,
  currentPoint: Point,
  bounds: Dimensions,
  minSize = 4,
): BoundingBox {
  let { x1, y1, x2, y2 } = initialBox;
  const targetX = Math.max(0, Math.min(currentPoint.x, bounds.width));
  const targetY = Math.max(0, Math.min(currentPoint.y, bounds.height));

  switch (handle) {
    case "nw":
      x1 = Math.min(targetX, x2 - minSize);
      y1 = Math.min(targetY, y2 - minSize);
      break;
    case "n":
      y1 = Math.min(targetY, y2 - minSize);
      break;
    case "ne":
      x2 = Math.max(targetX, x1 + minSize);
      y1 = Math.min(targetY, y2 - minSize);
      break;
    case "e":
      x2 = Math.max(targetX, x1 + minSize);
      break;
    case "se":
      x2 = Math.max(targetX, x1 + minSize);
      y2 = Math.max(targetY, y1 + minSize);
      break;
    case "s":
      y2 = Math.max(targetY, y1 + minSize);
      break;
    case "sw":
      x1 = Math.min(targetX, x2 - minSize);
      y2 = Math.max(targetY, y1 + minSize);
      break;
    case "w":
      x1 = Math.min(targetX, x2 - minSize);
      break;
  }

  return { x1, y1, x2, y2 };
}

/**
 * Constrains a bounding box to a specified aspect ratio (Width / Height).
 * Adjusts the dynamic edge while keeping the anchor edge stationary.
 *
 * @param box - Current candidate bounding box
 * @param targetRatio - Target aspect ratio (width / height, e.g. 1.0, 1.333, 1.777)
 * @param anchorHandle - The handle or anchor opposite to the movement
 * @param bounds - Boundary dimensions for clamping
 * @returns Aspect-ratio locked bounding box
 */
export function applyAspectRatio(
  box: BoundingBox,
  targetRatio: number,
  anchorHandle: ResizeHandle | "center" = "nw",
  bounds?: Dimensions,
): BoundingBox {
  if (targetRatio <= 0) return box;

  let width = Math.max(1, box.x2 - box.x1);
  let height = Math.max(1, box.y2 - box.y1);

  // Determine whether width or height should drive the adjustment
  if (width / height > targetRatio) {
    width = Math.round(height * targetRatio);
  } else {
    height = Math.round(width / targetRatio);
  }

  let { x1, y1 } = box;

  if (anchorHandle === "center") {
    const centerX = (box.x1 + box.x2) / 2;
    const centerY = (box.y1 + box.y2) / 2;
    x1 = Math.round(centerX - width / 2);
    y1 = Math.round(centerY - height / 2);
  } else {
    if (anchorHandle.includes("e")) {
      x1 = box.x2 - width;
    }
    if (anchorHandle.includes("s")) {
      y1 = box.y2 - height;
    }
  }

  const result: BoundingBox = {
    x1,
    y1,
    x2: x1 + width,
    y2: y1 + height,
  };

  return bounds ? clampRoiBox(result, bounds) : result;
}

/**
 * Translates (moves) a bounding box by delta offsets while preserving dimensions
 * and preventing out-of-bounds translation.
 *
 * @param box - Starting bounding box
 * @param delta - Translation vector (dx, dy)
 * @param bounds - Max boundaries (width, height)
 * @returns Translated bounding box clamped within bounds
 */
export function translateBoundingBox(
  box: BoundingBox,
  delta: Point,
  bounds: Dimensions,
): BoundingBox {
  const width = box.x2 - box.x1;
  const height = box.y2 - box.y1;

  let nextX1 = box.x1 + delta.x;
  let nextY1 = box.y1 + delta.y;

  // Boundary clamping
  nextX1 = Math.max(0, Math.min(nextX1, bounds.width - width));
  nextY1 = Math.max(0, Math.min(nextY1, bounds.height - height));

  return {
    x1: Math.round(nextX1),
    y1: Math.round(nextY1),
    x2: Math.round(nextX1 + width),
    y2: Math.round(nextY1 + height),
  };
}

/**
 * Calculates geometric and statistical properties of the Region of Interest.
 *
 * @param box - Bounding box in image pixel space
 * @param totalImageDims - Dimensions of the entire host image
 * @returns Structured ROI statistics including coverage percentage
 */
export function calculateRoiStatistics(
  box: BoundingBox,
  totalImageDims?: Dimensions,
): RoiStatistics {
  const width = Math.max(0, box.x2 - box.x1);
  const height = Math.max(0, box.y2 - box.y1);
  const areaPixels = width * height;
  const aspectRatio = height > 0 ? Number((width / height).toFixed(3)) : 0;

  let coveragePercentage = 0;
  if (totalImageDims && totalImageDims.width > 0 && totalImageDims.height > 0) {
    const totalArea = totalImageDims.width * totalImageDims.height;
    coveragePercentage = Number(((areaPixels / totalArea) * 100).toFixed(1));
  }

  return {
    width,
    height,
    areaPixels,
    aspectRatio,
    coveragePercentage,
  };
}
