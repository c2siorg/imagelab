export const filteringBlocks = [
  {
    type: "filtering_bilateral",
    message0: "Apply bilateral %1 no. of iterations %2 %3 Sigma color %4 %5 Sigma space %6",
    args0: [
      { type: "input_dummy" },
      { type: "field_number", name: "filterSize", value: 5, min: 0 },
      { type: "input_dummy" },
      { type: "field_number", name: "sigmaColor", value: 75, min: 0 },
      { type: "input_dummy" },
      { type: "field_number", name: "sigmaSpace", value: 75, min: 0 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip: "Applies bilateral filter"
  },
  {
    type: "filtering_boxfilter",
    message0: "Apply box filter with width %1 %2 , height %3 , depth %4 , pointX %5 , pointY %6",
    args0: [
      { type: "field_number", name: "width", value: 50, min: 0 },
      { type: "input_dummy" },
      { type: "field_number", name: "height", value: 50, min: 0 },
      { type: "field_number", name: "depth", value: 5, min: 0 },
      { type: "field_number", name: "point_x", value: -1 },
      { type: "field_number", name: "point_y", value: -1 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip: "Applies box filter"
  },
  {
    type: "filtering_pyramidup",
    message0: "Pyramid up",
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip: "Upsamples the image by 2x"
  },
  {
    type: "filtering_pyramiddown",
    message0: "Pyramid down",
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip: "Downsamples the image by 2x"
  },
  {
    type: "filtering_erosion",
    message0: "Apply erosion with %1 iterations %2 , pointX %3 , pointY %4",
    args0: [
      { type: "field_number", name: "iteration", value: 1, min: 0 },
      { type: "input_dummy" },
      { type: "field_number", name: "point_x", value: -1 },
      { type: "field_number", name: "point_y", value: -1 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip: "Applies erosion to the image"
  },
  {
    type: "filtering_dilation",
    message0: "Apply dilation with %1 iterations %2 , pointX %3 , pointY %4",
    args0: [
      { type: "field_number", name: "iteration", value: 1, min: 0 },
      { type: "input_dummy" },
      { type: "field_number", name: "point_x", value: -1 },
      { type: "field_number", name: "point_y", value: -1 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip: "Applies dilation to the image"
  },
  {
    type: "filtering_morphological",
    message0: "Apply morphological with %1 filter",
    args0: [
      {
        type: "field_dropdown",
        name: "type",
        options: [
          ["Tophat", "TOPHAT"],
          ["Close", "CLOSE"],
          ["Gradient", "GRADIENT"],
          ["Black hat", "BLACKHAT"],
          ["Open", "OPEN"]
        ]
      }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip: "Applies morphological operation"
  }
];
