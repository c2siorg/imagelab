export const thresholdingBlocks = [
  {
    type: "thresholding_applythreshold",
    message0: "Apply simple threshold with max value %1 and threshold value %2",
    args0: [
      { type: "field_number", name: "maxValue", value: 0, min: 0 },
      { type: "field_number", name: "thresholdValue", value: 0, min: 0 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "thresholding_style",
    tooltip: "Applies simple binary thresholding"
  },
  {
    type: "thresholding_adaptivethreshold",
    message0: "Apply adaptive threshold method %1 block size %2 C %3 max value %4",
    args0: [
      {
        type: "field_dropdown",
        name: "adaptiveMethod",
        options: [
          ["GAUSSIAN", "GAUSSIAN"],
          ["MEAN", "MEAN"]
        ]
      },
      { type: "field_number", name: "blockSize", value: 3, min: 3, precision: 1 },
      { type: "field_number", name: "cValue", value: 2 },
      { type: "field_number", name: "maxValue", value: 255, min: 0, max: 255 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "thresholding_style",
    tooltip: "Applies adaptive Gaussian or Mean thresholding - This method calculates the threshold for a pixel based on a small region around it, allowing for varying lighting conditions across the image. The 'maxValue' parameter sets the value to assign to pixels that exceed the threshold. This is particularly useful for images with uneven illumination."
  },
  {
    type: "thresholding_otsuthreshold",
    message0: "Apply Otsu threshold with max value %1",
    args0: [
      { type: "field_number", name: "maxValue", value: 255, min: 0, max: 255 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "thresholding_style",
    tooltip: "Automatically calculates optimal threshold using Otsu's method"
  },
  {
    type: "thresholding_applyborders",
    message0: "Apply borders %1",
    args0: [
      {
        type: "input_value",
        name: "border",
        check: ["border_for_all", "border_each_side"],
      },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "thresholding_style",
    tooltip: "Add a border around the image. Connect a border specification block. - This block allows you to add a border around the image. You can specify the border thickness using either the 'Same border thickness on all sides' block or the 'Set border thickness for each side individually' block. This is useful for framing the image or creating a visual separation from the background.",
  },
  {
    type: "border_for_all",
    message0: "with thickness %1",
    args0: [
      { type: "field_number", name: "border_all_sides", value: 2, min: 0 },
    ],
    output: "border_for_all",
    style: "thresholding_style",
    tooltip: "Same border thickness on all sides - Sets a uniform border thickness for all sides of the image. The 'border_all_sides' parameter specifies the thickness in pixels. This is a simple way to add a consistent border around the entire image.",
  },
  {
    type: "border_each_side",
    lastDummyAlign0: "CENTRE",
    message0: "with thickness %1 %2 %3 %4 %5 %6 %7",
    args0: [
      { type: "input_dummy", align: "CENTRE" },
      { type: "field_number", name: "borderTop", value: 2, min: 0 },
      { type: "input_dummy", align: "CENTRE" },
      { type: "field_number", name: "borderLeft", value: 2, min: 0 },
      { type: "field_number", name: "borderRight", value: 2, min: 0 },
      { type: "input_dummy", align: "CENTRE" },
      { type: "field_number", name: "borderBottom", value: 2, min: 0 },
    ],
    inputsInline: false,
    output: "border_each_side",
    style: "thresholding_style",
    tooltip: "Set border thickness for each side individually - Allows you to specify different border thicknesses for the top, left, right, and bottom sides of the image. Each 'border' parameter sets the thickness in pixels for its respective side. This is useful for creating asymmetrical borders or emphasizing specific edges of the image.",
  }
];
