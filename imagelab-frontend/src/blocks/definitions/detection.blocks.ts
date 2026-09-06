export const detectionBlocks = [
  {
    type: "detection_smiledetection",
    message0:
      "Detect smiles %1 Scale factor %2 %3 Min neighbors %4 %5 Min width %6 %7 Min height %8 %9 Box color %10 %11 Thickness %12 %13 Draw face boxes %14",
    args0: [
      { type: "input_dummy" },
      { type: "field_number", name: "scaleFactor", value: 1.1, min: 1.01, max: 2.0, precision: 0.01 },
      { type: "input_dummy" },
      { type: "field_number", name: "minNeighbors", value: 5, min: 1, max: 20 },
      { type: "input_dummy" },
      { type: "field_number", name: "minWidth", value: 30, min: 10, max: 500 },
      { type: "input_dummy" },
      { type: "field_number", name: "minHeight", value: 30, min: 10, max: 500 },
      { type: "input_dummy" },
      { type: "field_colour", name: "rgbcolors_input", colour: "#00ff00" },
      { type: "input_dummy" },
      { type: "field_number", name: "thickness", value: 2, min: 1, max: 10 },
      { type: "input_dummy" },
      { type: "field_checkbox", name: "drawFaceBoxes", checked: false },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "detection_style",
    tooltip:
      "Detects smiles in faces using Haar cascades - First detects faces, then searches for smiles only in the lower portion of each face to reduce false positives. Draws bounding boxes around detected smiles. Scale factor controls detection precision (smaller = slower but more accurate), min neighbors affects detection quality (higher = fewer false positives), and min width/height set minimum detection size. Enable 'Draw face boxes' to also show face bounding boxes.",
  },
];
