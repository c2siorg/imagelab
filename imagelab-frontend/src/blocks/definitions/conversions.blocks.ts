export const conversionsBlocks = [
  {
    type: "imageconvertions_grayimage",
    message0: "Gray the image",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts the image to grayscale"
  },
  {
    type: "imageconvertions_graytobinary",
    message0: "Convert grayscale image to a binary one %1 with threshold value %2 and max value %3",
    args0: [
      { type: "input_dummy" },
      { type: "field_number", name: "thresholdValue", value: 0, min: 0 },
      { type: "field_number", name: "maxValue", value: 0, min: 0 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts grayscale to binary using threshold"
  },
  {
    type: "imageconvertions_colormaps",
    message0: "Color map image with %1 filter",
    args0: [
      {
        type: "field_dropdown",
        name: "type",
        options: [
          ["Hot", "HOT"],
          ["Autumn", "AUTUMN"],
          ["Bone", "BONE"],
          ["Cool", "COOL"],
          ["HSV", "HSV"],
          ["JET", "JET"],
          ["Ocean", "OCEAN"],
          ["Parula", "PARULA"],
          ["Pink", "PINK"],
          ["Rainbow", "RAINBOW"],
        ],
      },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Apply different color maps to an image",
  },
  {
    type: "imageconvertions_colortobinary",
    message0: "Convert colored image to a binary one %1 by %2 type %3 with threshold value %4 and max value %5",
    args0: [
      { type: "input_dummy" },
      {
        type: "field_dropdown",
        name: "thresholdType",
        options: [
          ["Threshold Binary", "threshold_binary"],
          ["Threshold Binary Inv", "threshold_binary_inv"],
        ],
      },
      { type: "input_dummy" },
      { type: "field_number", name: "thresholdValue", value: 0, min: 0 },
      { type: "field_number", name: "maxValue", value: 0, min: 0 },
    ],
    inputsInline: false,
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Convert colored (RGB) image to binary with adjustable threshold",
  }
];
