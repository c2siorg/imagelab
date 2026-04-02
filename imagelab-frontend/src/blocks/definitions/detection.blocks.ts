export const detectionBlocks = [
  {
    type: "detection_eyedetection",
    message0: "Detect eyes scale factor %1 min neighbors %2 %3 min size %4 color %5 thickness %6",
    args0: [
      {
        type: "field_number",
        name: "scaleFactor",
        value: 1.2,
        min: 1.01,
        max: 2.0,
        precision: 0.01,
      },
      { type: "field_number", name: "minNeighbors", value: 8, min: 1, max: 20, precision: 1 },
      { type: "input_dummy" },
      { type: "field_number", name: "minSize", value: 24, min: 0, max: 2000, precision: 1 },
      { type: "field_colour", name: "rgbcolors_input", colour: "#00ff00" },
      { type: "field_number", name: "thickness", value: 10, min: 5, max: 20, precision: 1 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "detection_style",
    tooltip:
      "Detects eyes using an OpenCV Haar cascade and draws rectangles around matches. 'Scale factor' controls the image pyramid step size, 'min neighbors' filters weak detections, 'min size' ignores very small eyes, and 'thickness' sets the rectangle border width.",
  },
];
