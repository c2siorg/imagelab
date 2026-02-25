export const geometricBlocks = [
  {
    type: "geometric_reflectimage",
    message0: "Reflect image in %1 direction",
    args0: [
      {
        type: "field_dropdown",
        name: "type",
        options: [["X", "X"], ["Y", "Y"], ["Both", "Both"]]
      }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "geometric_style",
    tooltip: "Reflects the current image in the specified direction - Flips the image across the chosen axis. 'X' reflects the image vertically, 'Y' reflects it horizontally, and 'Both' reflects it across both axes. This transformation is useful for creating mirror images or correcting orientation."
  },
  {
    type: "geometric_rotateimage",
    message0: "Rotate image with angle of %1 and rescale by %2",
    args0: [
      { type: "field_angle", name: "angle", angle: 90 },
      { type: "field_number", name: "scale", value: 1, min: 0 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "geometric_style",
    tooltip: "Rotates the image by the given angle and rescales - Rotates the image by the specified angle in degrees (positive values rotate counter-clockwise) and rescales it by the given factor. This transformation is useful for correcting orientation, creating artistic effects, or preparing images for further analysis."
  },
  {
    type: "geometric_scaleimage",
    message0: "Scale Image by %1 in X axis and by %2 in Y axis",
    args0: [
      { type: "field_number", name: "fx", value: 1, min: 0 },
      { type: "field_number", name: "fy", value: 1, min: 0 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "geometric_style",
    tooltip: "Scales the image by the given factors - Resizes the image by scaling factors along the X and Y axes. A factor greater than 1 enlarges the image, while a factor between 0 and 1 reduces its size. This transformation is useful for resizing images for display, analysis, or to fit specific dimensions."
  },
  {
    type: "geometric_affineimage",
    message0: "Apply affine transformation",
    previousStatement: null,
    nextStatement: null,
    style: "geometric_style",
    tooltip: "Applies a fixed affine transformation (translate by 50, 100) - Transforms the image using a predefined affine transformation that translates the image by 50 pixels in the X direction and 100 pixels in the Y direction. This block is useful for demonstrating basic affine transformations, which can include translation, rotation, scaling, and shearing."
  }
];
