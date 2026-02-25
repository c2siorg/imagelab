export const sobelDerivativesBlocks = [
  {
    type: "sobelderivatives_soblederivate",
    message0: "Apply %1 sobel derivative with %2 depth",
    args0: [
      {
        type: "field_dropdown",
        name: "type",
        options: [
          ["Horizontal", "HORIZONTAL"],
          ["Vertical", "VERTICAL"],
          ["Both", "BOTH"],
        ],
      },
      { type: "field_number", name: "ddepth", value: 0, min: -10, max: 10 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "sobel_derivatives_style",
    tooltip: "Detect edges using Sobel derivative (first order) - Applies the Sobel operator to detect edges in the image. The 'type' parameter specifies the direction of the derivative: 'Horizontal' detects vertical edges, 'Vertical' detects horizontal edges, and 'Both' detects edges in both directions. The 'depth' parameter controls the depth of the output image; a value of 0 means the output will have the same depth as the source image.",
  },
  {
    type: "sobelderivatives_scharrderivate",
    message0: "Apply %1 scharr derivative with %2 depth",
    args0: [
      {
        type: "field_dropdown",
        name: "type",
        options: [
          ["Horizontal", "HORIZONTAL"],
          ["Vertical", "VERTICAL"],
        ],
      },
      { type: "field_number", name: "ddepth", value: 0, min: -10, max: 10 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "sobel_derivatives_style",
    tooltip: "Detect edges using Scharr derivative (second order) - Applies the Scharr operator, which is a more accurate version of the Sobel operator for edge detection. The 'type' parameter specifies the direction of the derivative: 'Horizontal' detects vertical edges and 'Vertical' detects horizontal edges. The 'depth' parameter controls the depth of the output image; a value of 0 means the output will have the same depth as the source image.",
  },
];
