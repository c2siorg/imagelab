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
    tooltip: "Applies bilateral filter - A non-linear, edge-preserving, and noise-reducing smoothing filter. It averages pixels based on both their spatial proximity and their intensity similarity, making it effective at reducing noise while keeping edges sharp. The 'filterSize' controls the size of the neighborhood, while 'sigmaColor' and 'sigmaSpace' adjust the degree of filtering based on color and spatial distance, respectively."
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
    tooltip: "Applies box filter - A simple linear filter that replaces each pixel with the average of its neighbors defined by the width and height. The 'depth' parameter controls the number of times the filter is applied, increasing the blurring effect. The anchor point (x, y) sets the filter center; use (-1, -1) to auto-center."
  },
  {
    type: "filtering_pyramidup",
    message0: "Pyramid up",
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip: "Upsamples the image by 2x - Increases the size of the image by a factor of 2 using Gaussian pyramid. This is useful for creating a smoother, higher-resolution version of the image, often used in multi-scale processing or to prepare an image for further analysis."
  },
  {
    type: "filtering_pyramiddown",
    message0: "Pyramid down",
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip: "Downsamples the image by 2x - Reduces the size of the image by a factor of 2 using Gaussian pyramid. This is useful for creating a smaller, lower-resolution version of the image, often used in multi-scale processing or to reduce computational load for further analysis."
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
    tooltip: "Applies erosion to the image - A morphological operation that erodes away the boundaries of foreground objects. It works by replacing each pixel with the minimum value of its neighbors defined by the structuring element. The 'iteration' parameter controls how many times the erosion is applied, increasing the effect. The anchor point (x, y) sets the filter center; use (-1, -1) to auto-center."
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
    tooltip: "Applies dilation to the image - A morphological operation that expands the boundaries of foreground objects. It works by replacing each pixel with the maximum value of its neighbors defined by the structuring element. The 'iteration' parameter controls how many times the dilation is applied, increasing the effect. The anchor point (x, y) sets the filter center; use (-1, -1) to auto-center."
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
    tooltip: "Applies morphological operation - Performs various morphological transformations based on the selected filter type. 'Open' removes small objects from the foreground, 'Close' fills small holes in the foreground, 'Gradient' highlights the edges of objects, 'Tophat' extracts small elements and details from the image, and 'Black hat' extracts small dark regions on a light background. These operations are useful for enhancing or suppressing specific features in an image."
  },{
    type: "filtering_sharpen",
    message0: "Apply sharpen with strength %1",
    args0: [
      { type: "field_number", name: "strength", value: 1.0, min: 0, max: 2, precision: 0.1 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip: "Applies image sharpening to enhance edges and details"
  }
];
