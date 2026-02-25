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
    tooltip: "Applies a simple blur to the image - Averages each pixel with its neighbors using a box of the given width and height to soften the image. The anchor point (x, y) sets the filter center; use (-1, -1) to auto-center."
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
    tooltip: "Applies Gaussian blur (width and height must be odd) - Uses a Gaussian function to blur the image, giving more weight to closer pixels. The kernel size (width and height) must be odd numbers (e.g., 1, 3, 5) to ensure a central pixel. This results in a smoother blur compared to a simple box blur."
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
    tooltip: "Applies median blur (kernel size must be odd) - Replaces each pixel with the median value of its neighbors defined by the kernel size. The kernel size must be an odd number (e.g., 1, 3, 5) to ensure a central pixel. This filter is effective at reducing salt-and-pepper noise while preserving edges."
  }
];
