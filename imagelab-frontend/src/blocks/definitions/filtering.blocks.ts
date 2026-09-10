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
      { type: "field_number", name: "sigmaSpace", value: 75, min: 0 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip:
      "Applies bilateral filter - A non-linear, edge-preserving, and noise-reducing smoothing filter. It averages pixels based on both their spatial proximity and their intensity similarity, making it effective at reducing noise while keeping edges sharp. The 'filterSize' controls the size of the neighborhood, while 'sigmaColor' and 'sigmaSpace' adjust the degree of filtering based on color and spatial distance, respectively.",
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
      { type: "field_number", name: "point_y", value: -1 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip:
      "Applies box filter - A simple linear filter that replaces each pixel with the average of its neighbors defined by the width and height. The 'depth' parameter controls the number of times the filter is applied, increasing the blurring effect. The anchor point (x, y) sets the filter center; use (-1, -1) to auto-center.",
  },
  {
    type: "filtering_pyramidup",
    message0: "Pyramid up",
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip:
      "Upsamples the image by 2x - Increases the size of the image by a factor of 2 using Gaussian pyramid. This is useful for creating a smoother, higher-resolution version of the image, often used in multi-scale processing or to prepare an image for further analysis.",
  },
  {
    type: "filtering_pyramiddown",
    message0: "Pyramid down",
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip:
      "Downsamples the image by 2x - Reduces the size of the image by a factor of 2 using Gaussian pyramid. This is useful for creating a smaller, lower-resolution version of the image, often used in multi-scale processing or to reduce computational load for further analysis.",
  },
  {
    type: "filtering_erosion",
    message0: "Apply erosion with %1 iterations %2 , pointX %3 , pointY %4",
    args0: [
      { type: "field_number", name: "iteration", value: 1, min: 0 },
      { type: "input_dummy" },
      { type: "field_number", name: "point_x", value: -1 },
      { type: "field_number", name: "point_y", value: -1 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip:
      "Applies erosion to the image - A morphological operation that erodes away the boundaries of foreground objects. It works by replacing each pixel with the minimum value of its neighbors defined by the structuring element. The 'iteration' parameter controls how many times the erosion is applied, increasing the effect. The anchor point (x, y) sets the filter center; use (-1, -1) to auto-center.",
  },
  {
    type: "filtering_dilation",
    message0: "Apply dilation with %1 iterations %2 , pointX %3 , pointY %4",
    args0: [
      { type: "field_number", name: "iteration", value: 1, min: 0 },
      { type: "input_dummy" },
      { type: "field_number", name: "point_x", value: -1 },
      { type: "field_number", name: "point_y", value: -1 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip:
      "Applies dilation to the image - A morphological operation that expands the boundaries of foreground objects. It works by replacing each pixel with the maximum value of its neighbors defined by the structuring element. The 'iteration' parameter controls how many times the dilation is applied, increasing the effect. The anchor point (x, y) sets the filter center; use (-1, -1) to auto-center.",
  },
  {
    type: "filtering_morphological",
    message0: "Apply morphological with %1 filter kernel size %2",
    args0: [
      {
        type: "field_dropdown",
        name: "type",
        options: [
          ["Tophat", "TOPHAT"],
          ["Close", "CLOSE"],
          ["Gradient", "GRADIENT"],
          ["Black hat", "BLACKHAT"],
          ["Open", "OPEN"],
        ],
      },
      { type: "field_number", name: "kernelSize", value: 5, min: 1, max: 99, precision: 1 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    extensions: ["odd_kernel_validator"],
    tooltip:
      "Applies morphological operation - Performs various morphological transformations based on the selected filter type. 'Open' removes small objects from the foreground, 'Close' fills small holes in the foreground, 'Gradient' highlights the edges of objects, 'Tophat' extracts small elements and details from the image, and 'Black hat' extracts small dark regions on a light background. Kernel size must be a positive odd integer and controls how strongly structures are affected. Even values are automatically rounded up to the nearest odd number.",
  },
  {
    type: "filtering_sharpen",
    message0: "Apply sharpen with strength %1",
    args0: [{ type: "field_number", name: "strength", value: 1.0, min: 0, max: 2, precision: 0.1 }],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip: "Applies image sharpening to enhance edges and details",
  },
  {
    type: "filtering_gaborfilter",
    message0:
      "Apply Gabor filter %1 kernel size %2 %3 sigma %4 %5 theta (deg) %6 %7 lambda %8 %9 gamma %10",
    args0: [
      { type: "input_dummy" },
      { type: "field_number", name: "kernelSize", value: 21, min: 1, precision: 1 },
      { type: "input_dummy" },
      { type: "field_number", name: "sigma", value: 5.0, min: 0.1, precision: 0.1 },
      { type: "input_dummy" },
      { type: "field_number", name: "theta", value: 0, min: 0, max: 180, precision: 1 },
      { type: "input_dummy" },
      { type: "field_number", name: "lambda_", value: 10.0, min: 1.0, precision: 0.5 },
      { type: "input_dummy" },
      { type: "field_number", name: "gamma", value: 0.5, min: 0.1, max: 1.0, precision: 0.1 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip:
      "Apply Gabor filter for texture detection - A Gabor filter is a Gaussian kernel modulated by a sinusoidal wave, making it highly sensitive to edges and textures at a specific orientation and frequency. 'Kernel size' controls the filter window (odd numbers only). 'Sigma' sets the width of the Gaussian envelope. 'Theta' (0–180°) selects the orientation — 0° targets horizontal edges, 90° targets vertical. 'Lambda' controls the texture frequency scale (higher = coarser textures). 'Gamma' adjusts the filter's aspect ratio. Useful for wood grain, fabric, fingerprint, and surface texture analysis.",
  },
  {
    type: "filtering_contourdetection",
    message0: "Draw Contours with mode %1 %2 method %3 %4 color %5 %6 thickness %7",
    args0: [
      {
        type: "field_dropdown",
        name: "mode",
        options: [
          ["External", "EXTERNAL"],
          ["Tree", "TREE"],
        ],
      },
      { type: "input_dummy" },
      {
        type: "field_dropdown",
        name: "method",
        options: [
          ["Simple", "SIMPLE"],
          ["None", "NONE"],
        ],
      },
      { type: "input_dummy" },
      { type: "field_colour", name: "rgbcolors_input", colour: "#00ff00" },
      { type: "input_dummy" },
      { type: "field_number", name: "thickness", value: 2, min: 1, max: 50 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip: "Detects contours on an image and renders them over the original graphic.",
  },
  {
    type: "filtering_cannyedge",
    message0: "Canny Edge Detection | threshold1 %1 threshold2 %2 aperture %3",
    args0: [
      { type: "field_number", name: "threshold1", value: 100, min: 0, max: 255 },
      { type: "field_number", name: "threshold2", value: 200, min: 0, max: 255 },
      {
        type: "field_dropdown",
        name: "apertureSize",
        options: [
          ["3", "3"],
          ["5", "5"],
          ["7", "7"],
        ],
      },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "filtering_style",
    tooltip:
      "Detects edges in the image using the Canny algorithm. threshold1 and threshold2 are the lower and upper bounds for the hysteresis procedure. apertureSize is the Sobel kernel size.",
  },
];
