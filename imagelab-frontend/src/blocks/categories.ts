export interface BlockInfo {
  type: string;
  label: string;
}

export interface CategoryInfo {
  name: string;
  icon: string;
  colour: string;
  blocks: BlockInfo[];
}

export const categories: CategoryInfo[] = [
  {
    name: "Basic",
    icon: "Image",
    colour: "#81C784",
    blocks: [
      { type: "basic_readimage", label: "Read Image" },
      { type: "basic_writeimage", label: "Write Image" }
    ]
  },
  {
    name: "Geometric",
    icon: "Move",
    colour: "#64B5F6",
    blocks: [
      { type: "geometric_reflectimage", label: "Reflect Image" },
      { type: "geometric_rotateimage", label: "Rotate Image" },
      { type: "geometric_affineimage", label: "Affine Transform" },
      { type: "geometric_scaleimage", label: "Scale Image" }
    ]
  },
  {
    name: "Conversions",
    icon: "Palette",
    colour: "#FF8A65",
    blocks: [
      { type: "imageconvertions_grayimage", label: "Gray Image" },
      { type: "imageconvertions_channelsplit", label: "Channel Split" },
      { type: "imageconvertions_graytobinary", label: "Gray to Binary" },
      { type: "imageconvertions_colormaps", label: "Color Maps" },
      { type: "imageconvertions_colortobinary", label: "Color to Binary" }
    ]
  },
  {
    name: "Drawing",
    icon: "Pencil",
    colour: "#BA68C8",
    blocks: [
      { type: "drawingoperations_drawline", label: "Draw Line" },
      { type: "drawingoperations_drawellipse", label: "Draw Ellipse" },
      { type: "drawingoperations_drawarrowline", label: "Draw Arrow Line" },
      { type: "drawingoperations_drawtext", label: "Draw Text" },
      { type: "drawingoperations_drawcircle", label: "Draw Circle" },
      { type: "drawingoperations_drawrectangle", label: "Draw Rectangle" }
    ]
  },
  {
    name: "Blurring",
    icon: "Droplets",
    colour: "#FFB74D",
    blocks: [
      { type: "blurring_applyblur", label: "Apply Blur" },
      { type: "blurring_applygaussianblur", label: "Gaussian Blur" },
      { type: "blurring_applymedianblur", label: "Median Blur" }
    ]
  },
  {
    name: "Filtering",
    icon: "Filter",
    colour: "#F06292",
    blocks: [
      { type: "filtering_bilateral", label: "Bilateral Filter" },
      { type: "filtering_sharpen", label: "Sharpen" },
      { type: "filtering_pyramidup", label: "Pyramid Up" },
      { type: "filtering_boxfilter", label: "Box Filter" },
      { type: "filtering_pyramiddown", label: "Pyramid Down" },
      { type: "filtering_erosion", label: "Erosion" },
      { type: "filtering_dilation", label: "Dilation" },
      { type: "filtering_morphological", label: "Morphological" }
    ]
  },
  {
    name: "Thresholding",
    icon: "SlidersHorizontal",
    colour: "#A1887F",
    blocks: [
      { type: "thresholding_adaptivethreshold", label: "Adaptive Threshold" },
      { type: "thresholding_applythreshold", label: "Apply Threshold" },
      { type: "thresholding_applyborders", label: "Apply Borders" },
      { type: "border_for_all", label: "Border (All Sides)" },
      { type: "border_each_side", label: "Border (Each Side)" },
      { type: "thresholding_otsuthreshold", label: "Otsu Threshold" },
    ]
  },
  {
    name: "Sobel Derivatives",
    icon: "Scan",
    colour: "#E57373",
    blocks: [
      { type: "sobelderivatives_soblederivate", label: "Sobel Derivative" },
      { type: "sobelderivatives_scharrderivate", label: "Scharr Derivative" }
    ]
  },
  {
    name: "Transformation",
    icon: "Shuffle",
    colour: "#4DB6AC",
    blocks: [
      { type: "transformation_distance", label: "Distance Transform" },
      { type: "transformation_laplacian", label: "Laplacian" }
    ]
  }
];