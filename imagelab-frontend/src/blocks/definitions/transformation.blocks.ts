export const transformationBlocks = [
  {
    type: "transformation_distance",
    message0: "Apply %1 distance with %2 depth",
    args0: [
      {
        type: "field_dropdown",
        name: "type",
        options: [
          ["DISTC", "DIST_C"],
          ["DISTL1", "DIST_L1"],
          ["DISTL2", "DIST_L2"],
          ["DISTLABEL_PIXEL", "DIST_LABEL_PIXEL"],
          ["DISTMASK_3", "DIST_MASK_3"],
        ],
      },
      { type: "field_number", name: "ddepth", value: 0, min: -10, max: 10 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "transformation_style",
    tooltip: "Apply distance transformation to a binary image",
  },
  {
    type: "transformation_laplacian",
    message0: "Apply laplacian with %1 depth",
    args0: [
      { type: "field_number", name: "ddepth", value: 0, min: -10, max: 10 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "transformation_style",
    tooltip: "Apply Laplacian edge detection (second order derivative)",
  },
];
