export const conversionsBlocks = [
  {
    type: "imageconversions_clahe",
    message0: "Apply CLAHE with clip limit %1 and tile grid size x: %2 y: %3",
    args0: [
      { type: "field_number", name: "clipLimit", value: 2.0, min: 0, max: 40 },
      { type: "field_number", name: "tileGridSizeX", value: 8, min: 1, max: 64, precision: 1 },
      { type: "field_number", name: "tileGridSizeY", value: 8, min: 1, max: 64, precision: 1 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip:
      "Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) to enhance local contrast in an image. The 'clipLimit' controls the amount of contrast enhancement, and 'tileGridSizeX' and 'tileGridSizeY' define the grid size for local histogram equalization.",
  },
  {
    type: "imageconversions_grayimage",
    message0: "Gray the image",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts the image to grayscale",
  },
  {
    type: "imageconversions_channelsplit",
    message0: "Extract %1 channel from image",
    args0: [
      {
        type: "field_dropdown",
        name: "channel",
        options: [
          ["Red", "RED"],
          ["Green", "GREEN"],
          ["Blue", "BLUE"],
        ],
      },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Splits a multi-channel image and extracts the selected channel as grayscale",
  },
  {
    type: "imageconversions_graytobinary",
    message0: "Convert grayscale image to a binary one %1 with threshold value %2 and max value %3",
    args0: [
      { type: "input_dummy" },
      { type: "field_number", name: "thresholdValue", value: 0, min: 0 },
      { type: "field_number", name: "maxValue", value: 255, min: 0 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip:
      "Converts grayscale to binary using threshold - Applies a binary threshold to a grayscale image, converting it to black and white. Pixels with intensity above the threshold value will be set to the max value (white), while those below will be set to 0 (black). This is useful for segmenting objects from the background.",
  },
  {
    type: "imageconversions_invertimage",
    message0: "Invert image",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip:
      "Inverts all pixel values in the image - Applies a bitwise NOT to every pixel, replacing each value with 255 minus itself. Bright regions become dark, dark regions become bright, and colours shift to their complementary opposites. Useful for creating negative-style images or improving visibility of certain features before thresholding.",
  },
  {
    type: "imageconversions_colormaps",
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
    tooltip:
      "Apply different color maps to an image - Transforms the colors of an image using various color maps. This can enhance visual contrast and highlight specific features. For example, the 'JET' colormap transitions from blue to red, while 'HSV' represents hue, saturation, and value. Choose a colormap that best suits your image analysis needs.",
  },
  {
    type: "imageconversions_brightnessandcontrast",
    message0: "Adjust image brightness by %1 and contrast scale by %2",
    args0: [
      { type: "field_number", name: "brightnessValue", value: 0, min: -100, max: 100 },
      { type: "field_number", name: "contrastValue", value: 1.0, min: 0.0, max: 3.0 },
    ],
    inputsInline: false,
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip:
      "Adjusts the brightness and contrast of an image - Brightness controls the overall lightness or darkness of an image, while contrast controls the difference in intensity between different parts of the image. Increasing brightness makes the image lighter, and increasing contrast makes the differences between light and dark areas more pronounced.",
  },
  {
    type: "imageconversions_colortobinary",
    message0:
      "Convert colored image to a binary one %1 by %2 type %3 with threshold value %4 and max value %5",
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
      { type: "field_number", name: "maxValue", value: 255, min: 0 },
    ],
    inputsInline: false,
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip:
      "Convert colored (RGB) image to binary with adjustable threshold - Applies a binary threshold to a colored image, converting it to black and white. You can choose between 'Threshold Binary' (pixels above the threshold become white) and 'Threshold Binary Inv' (pixels above the threshold become black). Adjust the threshold value to control which pixels are considered foreground (white) or background (black), and set the max value for the output binary image.",
  },
  {
    type: "imageconversions_histogramequalization",
    message0: "Enhance contrast using histogram equalization",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Automatically improves image contrast using histogram equalization",
  },
  {
    type: "imageconversions_bgrtohsv",
    message0: "Convert BGR to HSV",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts an image from BGR to HSV color space (separates color from brightness).",
  },
  {
    type: "imageconversions_hsvtobgr",
    message0: "Convert HSV to BGR",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts an image from HSV back to BGR color space.",
  },
  {
    type: "imageconversions_bgrtolab",
    message0: "Convert BGR to LAB",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts BGR to LAB color space (approximates human vision).",
  },
  {
    type: "imageconversions_labtobgr",
    message0: "Convert LAB to BGR",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts LAB back to BGR color space.",
  },
  {
    type: "imageconversions_bgrtoycrcb",
    message0: "Convert BGR to YCrCb",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts BGR to YCrCb color space (separates luma from chroma).",
  },
  {
    type: "imageconversions_ycrcbtobgr",
    message0: "Convert YCrCb to BGR",
    previousStatement: null,
    nextStatement: null,
    style: "conversions_style",
    tooltip: "Converts YCrCb back to BGR color space.",
  },
];

/**
 * Deliberate legacy alias table for backward compatibility with saved workspaces
 */
export const LEGACY_CONVERSION_ALIASES: Record<string, string> = {
  imageconvertions_clahe: "imageconversions_clahe",
  imageconvertions_grayimage: "imageconversions_grayimage",
  imageconvertions_channelsplit: "imageconversions_channelsplit",
  imageconvertions_graytobinary: "imageconversions_graytobinary",
  imageconvertions_invertimage: "imageconversions_invertimage",
  imageconvertions_colormaps: "imageconversions_colormaps",
  imageconvertions_brightnessandcontrast: "imageconversions_brightnessandcontrast",
  imageconvertions_colortobinary: "imageconversions_colortobinary",
  imageconvertions_histogramequalization: "imageconversions_histogramequalization",
  imageconvertions_bgrtohsv: "imageconversions_bgrtohsv",
  imageconvertions_hsvtobgr: "imageconversions_hsvtobgr",
  imageconvertions_bgrtolab: "imageconversions_bgrtolab",
  imageconvertions_labtobgr: "imageconversions_labtobgr",
  imageconvertions_bgrtoycrcb: "imageconversions_bgrtoycrcb",
  imageconvertions_ycrcbtobgr: "imageconversions_ycrcbtobgr",
};

export function resolveOperatorName(blockType: string): string {
  return LEGACY_CONVERSION_ALIASES[blockType] ?? blockType;
}

export const legacyConversionBlocks = Object.entries(LEGACY_CONVERSION_ALIASES).map(
  ([legacyType, canonicalType]) => {
    const canonicalDef = conversionsBlocks.find((b) => b.type === canonicalType);
    return {
      ...canonicalDef,
      type: legacyType,
    };
  },
);
