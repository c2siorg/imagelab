export const transformationBlocks = [
  {
    type: "transformation_distance",
    message0: "Apply %1 distance with %2 depth",
    args0: [
      {
        type: "field_dropdown",
        name: "type",
        options: [
          ["DISTC", "DIST_C"],
          ["DISTL1", "DIST_L1"],
          ["DISTL2", "DIST_L2"],
          ["DISTLABEL_PIXEL", "DIST_LABEL_PIXEL"],
          ["DISTMASK_3", "DIST_MASK_3"],
        ],
      },
      { type: "field_number", name: "ddepth", value: 0, min: -10, max: 10 },
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
