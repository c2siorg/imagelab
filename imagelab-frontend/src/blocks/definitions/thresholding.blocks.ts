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
    message0: "Apply adaptive threshold with max value %1",
    args0: [
      { type: "field_number", name: "maxValue", value: 0, min: 0 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "thresholding_style",
    tooltip: "Applies adaptive Gaussian thresholding"
  },
  {
    type: "thresholding_otsuthreshold",
    message0: "Apply Otsu threshold with max value %1",
    args0: [
      { type: "field_number", name: "maxValue", value: 255, min: 0, max:255 }
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
    tooltip: "Add a border around the image. Connect a border specification block.",
  },
  {
    type: "border_for_all",
    message0: "with thickness %1",
    args0: [
      { type: "field_number", name: "border_all_sides", value: 2, min: 0 },
    ],
    output: "border_for_all",
    style: "thresholding_style",
    tooltip: "Same border thickness on all sides",
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
    tooltip: "Set border thickness for each side individually",
  }
];
