export const transformationBlocks = [
  {
    type: "transformation_minenclosing",
    message0:
      "Minimum enclosing %1 Geometry %2 %3 Min area %4 %5 Box color %6 %7 Circle color %8 %9 Ellipse color %10 %11 Thickness %12 %13 Show contours %14",
    args0: [
      { type: "input_dummy" },
      {
        type: "field_dropdown",
        name: "geometry",
        options: [
          ["Rotated Box", "ROTATED_BOX"],
          ["Enclosing Circle", "ENCLOSING_CIRCLE"],
          ["Fit Ellipse", "FIT_ELLIPSE"],
          ["All Shapes", "ALL_SHAPES"],
        ],
      },
      { type: "input_dummy" },
      { type: "field_number", name: "min_area", value: 50, min: 0, max: 100000 },
      { type: "input_dummy" },
      { type: "field_colour", name: "box_color", colour: "#00ffff" },
      { type: "input_dummy" },
      { type: "field_colour", name: "circle_color", colour: "#ff00ff" },
      { type: "input_dummy" },
      { type: "field_colour", name: "ellipse_color", colour: "#ffff00" },
      { type: "input_dummy" },
      { type: "field_number", name: "thickness", value: 2, min: 1, max: 20 },
      { type: "input_dummy" },
      { type: "field_checkbox", name: "show_contours", checked: false },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "transformation_style",
    tooltip:
      "Calculates and renders minimum enclosing and bounding geometries around detected shapes: rotated minimum-area bounding boxes (cv2.minAreaRect), minimum enclosing circles (cv2.minEnclosingCircle), and fitted bounding ellipses (cv2.fitEllipse). Operates on binary, thresholded, or high-contrast edge imagery. Ideal for object orientation measurement, particle sizing, aspect ratio calculation, and geometric shape classification.",
  },
  {
    type: "transformation_convexhull",
    message0:
      "Convex hull %1 Mode %2 %3 Min area %4 %5 Min defect depth %6 %7 Hull color %8 %9 Defect color %10 %11 Thickness %12 %13 Show contours %14",
    args0: [
      { type: "input_dummy" },
      {
        type: "field_dropdown",
        name: "mode",
        options: [
          ["Hull and Defects", "HULL_AND_DEFECTS"],
          ["Hull Only", "HULL_ONLY"],
        ],
      },
      { type: "input_dummy" },
      { type: "field_number", name: "min_area", value: 50, min: 0, max: 100000 },
      { type: "input_dummy" },
      {
        type: "field_number",
        name: "min_defect_depth",
        value: 5,
        min: 0,
        max: 500,
        precision: 0.1,
      },
      { type: "input_dummy" },
      { type: "field_colour", name: "hull_color", colour: "#00ffff" },
      { type: "input_dummy" },
      { type: "field_colour", name: "defect_color", colour: "#ff0000" },
      { type: "input_dummy" },
      { type: "field_number", name: "thickness", value: 2, min: 1, max: 20 },
      { type: "input_dummy" },
      { type: "field_checkbox", name: "show_contours", checked: false },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "transformation_style",
    tooltip:
      "Computes the minimal enclosing convex hull and convexity defects (cavities/indentations) for foreground shapes in an image. Expects binary, thresholded, or high-contrast edge input (e.g. preceded by a Threshold or Canny Edge block), as raw photographic images without zero-background pixels treat the whole frame as one contour. Extracts external contours, computes the minimal enclosing convex polygon, and detects indentation points where the shape departs from the hull. Useful for hand gesture recognition, finger counting, and object shape analysis.",
  },
  {
    type: "transformation_distance",
    message0: "Apply %1 distance transform",
    args0: [
      {
        type: "field_dropdown",
        name: "type",
        options: [
          ["DIST_C", "DIST_C"],
          ["DIST_L1", "DIST_L1"],
          ["DIST_L2", "DIST_L2"],
        ],
      },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "transformation_style",
    tooltip:
      "Apply distance transformation to a binary image - Applies a distance transformation to a binary image, where each pixel is assigned a value based on its distance to the nearest zero pixel. This is useful for shape analysis and feature detection.",
  },
  {
    type: "transformation_laplacian",
    message0: "Apply Laplacian with kernel size %1 and output depth %2",
    args0: [
      {
        type: "field_dropdown",
        name: "ksize",
        options: [
          ["1 (finest)", "1"],
          ["3", "3"],
          ["5", "5"],
          ["7 (broadest)", "7"],
        ],
      },
      { type: "field_number", name: "ddepth", value: -1, min: -1, max: 6, precision: 1 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "transformation_style",
    tooltip:
      "Apply Laplacian edge detection (second order derivative) - Detects regions of rapid intensity change. Kernel size controls the aperture (1, 3, 5, or 7) — larger values detect broader edges. Output depth: use -1 to match the source image depth (note: for 8-bit images, negative Laplacian responses are clipped to zero — use depth 6 / CV_64F to retain full signed output). Values 0–6 correspond to OpenCV depth constants. Useful for blob detection and sharpening edge transitions.",
  },
];
