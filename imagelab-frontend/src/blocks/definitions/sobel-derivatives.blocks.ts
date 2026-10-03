export const sobelDerivativesBlocks = [
  {
    type: "sobelderivatives_soblederivate",
    message0: "Apply %1 sobel derivative",
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
    ],
    previousStatement: null,
    nextStatement: null,
    style: "sobel_derivatives_style",
    tooltip:
      "Detect edges using Sobel derivative (first order) - Applies the Sobel operator to detect edges in the image. The 'type' parameter specifies the direction of the derivative: 'Horizontal' detects vertical edges, 'Vertical' detects horizontal edges, and 'Both' detects edges in both directions using the L2 gradient magnitude. The output is always a uint8 image.",
  },
  {
    type: "sobelderivatives_scharrderivate",
    message0: "Apply %1 scharr derivative",
    args0: [
      {
        type: "field_dropdown",
        name: "type",
        options: [
          ["Horizontal", "HORIZONTAL"],
          ["Vertical", "VERTICAL"],
        ],
      },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "sobel_derivatives_style",
    tooltip:
      "Detect edges using Scharr derivative (first order) - Applies the Scharr operator, which is a more accurate first-order derivative operator than Sobel due to its optimized kernel weights. The 'type' parameter specifies the direction: 'Horizontal' detects vertical edges and 'Vertical' detects horizontal edges. The output is always a uint8 image.",
  },
  {
    type: "sobelderivatives_prewittoperator",
    message0: "Apply Prewitt edge detection",
    previousStatement: null,
    nextStatement: null,
    style: "sobel_derivatives_style",
    tooltip:
      "Detect edges using the Prewitt operator - Applies two 3x3 kernels to compute horizontal and vertical gradient magnitude. Similar to Sobel but with equal weights across all rows/columns, making it slightly simpler and faster. Colour images are converted to grayscale automatically.",
  },
  {
    type: "sobelderivatives_robertsoperator",
    message0: "Apply Roberts Cross edge detection",
    previousStatement: null,
    nextStatement: null,
    style: "sobel_derivatives_style",
    tooltip:
      "Detect edges using the Roberts Cross operator - Applies two 2x2 diagonal kernels to compute gradient magnitude. It is the smallest and cheapest of the classical edge detectors, but it is also the most directionally biased: the two kernels measure contrast along the image diagonals, so horizontal and vertical edges respond most strongly (peak = contrast x sqrt(2)) while edges running along the diagonals respond about 29% more weakly. The tiny 2x2 support also makes it noise-sensitive, so it needs sharp, high-contrast edges to respond at all. Colour images are converted to grayscale automatically.",
  },
];
