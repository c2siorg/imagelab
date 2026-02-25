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
    type: "imageconvertions_channelsplit",
    message0: "Extract %1 channel from image",
    args0: [
      {
        type: "field_dropdown",
        name: "channel",
        options: [
          ["Red", "RED"],
          ["Green", "GREEN"],
          ["Blue", "BLUE"]
        ]
      }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Splits a multi-channel image and extracts the selected channel as grayscale"
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
    tooltip: "Converts grayscale to binary using threshold - Applies a binary threshold to a grayscale image, converting it to black and white. Pixels with intensity above the threshold value will be set to the max value (white), while those below will be set to 0 (black). This is useful for segmenting objects from the background."
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
    tooltip: "Apply different color maps to an image - Transforms the colors of an image using various color maps. This can enhance visual contrast and highlight specific features. For example, the 'JET' colormap transitions from blue to red, while 'HSV' represents hue, saturation, and value. Choose a colormap that best suits your image analysis needs.",
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
    tooltip: "Convert colored (RGB) image to binary with adjustable threshold - Applies a binary threshold to a colored image, converting it to black and white. You can choose between 'Threshold Binary' (pixels above the threshold become white) and 'Threshold Binary Inv' (pixels above the threshold become black). Adjust the threshold value to control which pixels are considered foreground (white) or background (black), and set the max value for the output binary image.",
  },
  {
    type: "imageconvertions_bgrtohsv",
    message0: "Convert BGR to HSV",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts an image from BGR to HSV color space (separates color from brightness)."
  },
  {
    type: "imageconvertions_hsvtobgr",
    message0: "Convert HSV to BGR",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts an image from HSV back to BGR color space."
  },
  {
    type: "imageconvertions_bgrtolab",
    message0: "Convert BGR to LAB",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts BGR to LAB color space (approximates human vision)."
  },
  {
    type: "imageconvertions_labtobgr",
    message0: "Convert LAB to BGR",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts LAB back to BGR color space."
  },
  {
    type: "imageconvertions_bgrtoycrcb",
    message0: "Convert BGR to YCrCb",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts BGR to YCrCb color space (separates luma from chroma)."
  },
  {
    type: "imageconvertions_ycrcbtobgr",
    message0: "Convert YCrCb to BGR",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts YCrCb back to BGR color space."
  }
];
