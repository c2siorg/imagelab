export const segmentationBlocks = [
  {
    type: "segmentation_watershed",
    message0: "Watershed Segmentation %1 Foreground Threshold %2",
    args0: [
      { type: "input_dummy" },
      {
        type: "field_number",
        name: "foreground_threshold",
        value: 0.5,
        min: 0.1,
        max: 0.9,
        precision: 0.1,
      },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "segmentation_style",
    tooltip:
      "Applies watershed segmentation - A classical algorithm that treats the image like a topographic map, flooding basins from marker points to separate distinct regions. The foreground threshold (0.1–0.9) controls how confidently a region must stand out to be treated as foreground. Segment boundaries are highlighted in red. Note: assumes foreground objects are darker than the background (e.g. cells, text). For bright-on-dark images the foreground/background logic will be inverted.",
  },
  {
    type: "segmentation_kmeans",
    message0:
      "K-Means Segmentation %1 Number of clusters (K) %2 %3 Max iterations %4 %5 Epsilon %6",
    args0: [
      { type: "input_dummy" },
      { type: "field_number", name: "k", value: 3, min: 2, max: 10 },
      { type: "input_dummy" },
      { type: "field_number", name: "max_iter", value: 100, min: 1, max: 500 },
      { type: "input_dummy" },
      {
        type: "field_number",
        name: "epsilon",
        value: 0.2,
        min: 0.01,
        max: 10.0,
        precision: 0.01,
      },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "segmentation_style",
    tooltip:
      "Applies K-Means color segmentation - Groups pixels into K clusters based on color similarity, replacing each pixel with the average color of its cluster. K controls the number of color segments (2–10). Higher K values produce more detailed segmentation. Max iterations (1–500) and epsilon (0.01–10.0) control the convergence of the algorithm. Great for simplifying images and understanding dominant color regions.",
  },
  {
    type: "segmentation_meanshift",
    message0:
      "Apply Mean Shift Segmentation %1 spatial radius %2 %3 colour radius %4 %5 max level %6",
    args0: [
      { type: "input_dummy" },
      { type: "field_number", name: "sp", value: 21, min: 1, precision: 1 },
      { type: "input_dummy" },
      { type: "field_number", name: "sr", value: 51, min: 1, precision: 1 },
      { type: "input_dummy" },
      { type: "field_number", name: "maxLevel", value: 1, min: 0, max: 4, precision: 1 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "segmentation_style",
    tooltip:
      "Apply Mean Shift Segmentation for colour-based region clustering - Groups pixels with similar colours and spatial proximity into flat regions, producing a simplified, posterised version of the image with preserved edges. 'Spatial radius' controls how far away in pixel distance neighbours are considered. 'Colour radius' controls how different in colour a pixel can be and still be merged — higher values produce larger, more uniform regions. 'Max level' sets the pyramid depth for multi-scale processing (0–4).",
  },
];
