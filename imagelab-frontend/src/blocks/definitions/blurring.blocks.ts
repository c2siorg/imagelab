export const blurringBlocks = [
  {
    type: "blurring_applyblur",
    message0: "Apply Blur with width %1 , height %2 %3 from point x %4 and y %5",
    args0: [
      { type: "field_number", name: "widthSize", value: 3, min: 0 },
      { type: "field_number", name: "heightSize", value: 3, min: 0 },
      { type: "input_dummy" },
      { type: "field_number", name: "pointX", value: -1 },
      { type: "field_number", name: "pointY", value: -1 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "blurring_style",
    tooltip: "Applies a simple blur to the image"
  },
  {
    type: "blurring_applygaussianblur",
    message0: "Apply gaussian Blur with width %1 , height %2",
    args0: [
      { type: "field_number", name: "widthSize", value: 1, min: 1 },
      { type: "field_number", name: "heightSize", value: 1, min: 1 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "blurring_style",
    tooltip: "Applies Gaussian blur (width and height must be odd)"
  },
  {
    type: "blurring_applymedianblur",
    message0: "Apply median Blur with kernel value of %1",
    args0: [
      { type: "field_number", name: "kernelSize", value: 5, min: 1 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "blurring_style",
    tooltip: "Applies median blur (kernel size must be odd)"
  }
];
