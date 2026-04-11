export const detectionBlocks = [
  {
    type: "detection_smiledetection",
    message0: "Detect smiles scale factor %1 min neighbors %2 %3 min size %4 color %5 thickness %6",
    args0: [
      {
        type: "field_number",
        name: "scaleFactor",
        value: 1.6,
        min: 1.01,
        max: 3.0,
        precision: 0.01,
      },
      { type: "field_number", name: "minNeighbors", value: 18, min: 1, max: 40, precision: 1 },
      { type: "input_dummy" },
      { type: "field_number", name: "minSize", value: 24, min: 0, max: 2000, precision: 1 },
      { type: "field_colour", name: "rgbcolors_input", colour: "#00ff00" },
      { type: "field_number", name: "thickness", value: 15, min: 1, max: 45, precision: 1 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "detection_style",
    tooltip:
      "Detects smiles using OpenCV Haar cascades. The operator first finds faces, then searches only within the lower face region for likely smiles. 'Scale factor' controls the smile search pyramid step size, 'min neighbors' filters weak detections, 'min size' ignores very small smiles, and 'thickness' sets the rectangle border width.",
  },
];
