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
    tooltip: "Reflects the current image in the specified direction"
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
    tooltip: "Rotates the image by the given angle and rescales"
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
    tooltip: "Scales the image by the given factors"
  },
  {
    type: "geometric_affineimage",
    message0: "Apply affine transformation",
    previousStatement: null,
    nextStatement: null,
    style: "geometric_style",
    tooltip: "Applies a fixed affine transformation (translate by 50, 100)"
  }
];
