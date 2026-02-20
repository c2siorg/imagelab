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
    tooltip: "Detect edges using Sobel derivative (first order)",
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
    tooltip: "Detect edges using Scharr derivative (second order)",
  },
];
