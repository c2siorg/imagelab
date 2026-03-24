export const detectionBlocks = [
  {
    type: "detection_facedetection",
    message0: "Detect faces scale factor %1 min neighbors %2 %3 min size %4 color %5 thickness %6",
    args0: [
      {
        type: "field_number",
        name: "scaleFactor",
        value: 1.3,
        min: 1.01,
        max: 2.0,
        precision: 0.01,
      },
      { type: "field_number", name: "minNeighbors", value: 6, min: 1, max: 20, precision: 1 },
      { type: "input_dummy" },
      { type: "field_number", name: "minSize", value: 80, min: 0, max: 2000, precision: 1 },
      { type: "field_colour", name: "rgbcolors_input", colour: "#00ff00" },
      { type: "field_number", name: "thickness", value: 2, min: 1, max: 20, precision: 1 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "detection_style",
    tooltip:
      "Detects human faces using an OpenCV Haar cascade and draws rectangles around matches. 'Scale factor' controls the image pyramid step size, 'min neighbors' filters weak detections, 'min size' ignores very small faces, and 'thickness' sets the rectangle border width.",
  },
];
