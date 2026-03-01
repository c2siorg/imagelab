export interface OperatorParameter {
  name: string;
  description: string;
}

export interface OperatorDoc {
  type: string;
  name: string;
  description: string;
  parameters: OperatorParameter[];
  formula?: string;
  useCases: string[];
}

export const operatorDocs: Record<string, OperatorDoc> = {
  // --- Basic ---
  basic_readimage: {
    type: "basic_readimage",
    name: "Read Image",
    description: "Loads an image from a specified file path into the memory grid.",
    parameters: [
      { name: "Image Path", description: "Absolute or relative path to the image file." },
    ],
    useCases: ["Starting point for any image processing pipeline."],
  },
  basic_writeimage: {
    type: "basic_writeimage",
    name: "Write Image",
    description: "Saves the processed image matrix back to the disk.",
    parameters: [
      { name: "Output Path", description: "Path where the output image should be saved." },
    ],
    useCases: ["Finalizing a pipeline to export the processed result."],
  },

  // --- Geometric ---
  geometric_reflectimage: {
    type: "geometric_reflectimage",
    name: "Reflect Image",
    description: "Flips a 2D array around vertical, horizontal, or both axes.",
    parameters: [
      { name: "Flip Code", description: "0 for X-axis, >0 for Y-axis, <0 for both axes." },
    ],
    useCases: ["Data augmentation, correcting upside-down images."],
  },
  geometric_cropimage: {
    type: "geometric_cropimage",
    name: "Crop Image",
    description: "Extracts a rectangular region of interest (ROI) from the image.",
    parameters: [
      { name: "X, Y", description: "Top-left coordinates for the crop area." },
      { name: "Width, Height", description: "Dimensions of the cropped bounding box." },
    ],
    useCases: ["Isolating specific objects, removing image borders."],
  },
  geometric_rotateimage: {
    type: "geometric_rotateimage",
    name: "Rotate Image",
    description:
      "Rotates the image by a specified angle around a chosen center point using an affine transformation.",
    parameters: [
      { name: "Angle", description: "Rotation angle in degrees." },
      { name: "Scale", description: "Isotropic scale factor applied during rotation." },
    ],
    useCases: ["Correcting skew, data augmentation."],
  },
  geometric_affineimage: {
    type: "geometric_affineimage",
    name: "Affine Transform",
    description: "Applies a 2x3 affine transformation matrix to warp the image.",
    parameters: [
      {
        name: "Points",
        description: "Three points in the original image mapped to three points in the output.",
      },
    ],
    useCases: ["Perspective correction, scaling, and skewing."],
  },
  geometric_scaleimage: {
    type: "geometric_scaleimage",
    name: "Scale Image",
    description: "Resizes the image to specified dimensions or scale factors using interpolation.",
    parameters: [
      {
        name: "Scale X, Scale Y",
        description: "Scaling factors along the horizontal and vertical axes.",
      },
    ],
    useCases: ["Making images uniform for neural networks, creating thumbnails."],
  },

  // --- Conversions ---
  imageconvertions_grayimage: {
    type: "imageconvertions_grayimage",
    name: "Color to Grayscale",
    description:
      "Converts a multi-channel RGB/BGR image into a single-channel grayscale image. Uses the standard weighted luminosity method.",
    parameters: [],
    formula: "Y = 0.299*R + 0.587*G + 0.114*B",
    useCases: [
      "Removing color noise, decreasing computational load, preparing for edge detection.",
    ],
  },
  imageconvertions_channelsplit: {
    type: "imageconvertions_channelsplit",
    name: "Channel Split",
    description: "Splits a multi-channel image into several single-channel image layers.",
    parameters: [],
    useCases: ["Analyzing individual R, G, B channels, applying filters to specific color bands."],
  },
  imageconvertions_graytobinary: {
    type: "imageconvertions_graytobinary",
    name: "Gray to Binary",
    description:
      "Applies a threshold to turn a grayscale image into a pure black and white (binary) image.",
    parameters: [
      {
        name: "Threshold Value",
        description: "Pixel values above this threshold become maximal (255), otherwise 0.",
      },
    ],
    formula: "dst(x,y) = maxVal if src(x,y) > thresh else 0",
    useCases: ["Creating masks, separating foreground objects from background."],
  },
  imageconvertions_colormaps: {
    type: "imageconvertions_colormaps",
    name: "Color Maps",
    description:
      "Applies a pseudo-color map to a grayscale image to enhance visual perception of intensity.",
    parameters: [
      { name: "Color Map Type", description: "Select the colormap style (e.g., JET, HOT, BONE)." },
    ],
    useCases: ["Visualizing depth maps, temperature distribution, or heatmaps."],
  },
  imageconvertions_colortobinary: {
    type: "imageconvertions_colortobinary",
    name: "Color to Binary",
    description:
      "Directly converts a color image to a binary mask using predefined threshold configurations.",
    parameters: [
      { name: "Threshold Type", description: "Algorithm to isolate background from foreground." },
    ],
    useCases: ["Feature extraction where color is irrelevant."],
  },

  // --- Drawing ---
  drawingoperations_drawline: {
    type: "drawingoperations_drawline",
    name: "Draw Line",
    description: "Draws a straight line segment connecting two points on the image.",
    parameters: [
      { name: "Start Point", description: "X, Y coordinates for line start." },
      { name: "End Point", description: "X, Y coordinates for line end." },
      { name: "Color", description: "RGB value of the line." },
      { name: "Thickness", description: "Line width in pixels." },
    ],
    useCases: ["Highlighting vectors, drawing bounding box edges."],
  },
  drawingoperations_drawellipse: {
    type: "drawingoperations_drawellipse",
    name: "Draw Ellipse",
    description: "Draws a simple or thick elliptic arc or a solid ellipse section.",
    parameters: [
      { name: "Center", description: "X, Y coordinates of the ellipse center." },
      { name: "Axes", description: "Lengths of the major and minor axes." },
      { name: "Angle", description: "Ellipse rotation angle in degrees." },
    ],
    useCases: ["Highlighting circular or oval objects in an image."],
  },
  drawingoperations_drawarrowline: {
    type: "drawingoperations_drawarrowline",
    name: "Draw Arrow Line",
    description: "Draws an arrow segment pointing from the first point to the second point.",
    parameters: [{ name: "Start/End Points", description: "Tail and head of the arrow." }],
    useCases: ["Showing direction of motion, visualizing gradients."],
  },
  drawingoperations_drawtext: {
    type: "drawingoperations_drawtext",
    name: "Draw Text",
    description: "Renders fixed-size text strings over the image using OpenCV's built-in fonts.",
    parameters: [
      { name: "Text", description: "String to render." },
      { name: "Origin", description: "Bottom-left corner of the text string in the image." },
      { name: "Font Scale", description: "Font size multiplier." },
    ],
    useCases: ["Adding watermarks, labeling objects, overlaying debug data."],
  },
  drawingoperations_drawcircle: {
    type: "drawingoperations_drawcircle",
    name: "Draw Circle",
    description: "Draws a circle with a given center and radius.",
    parameters: [
      { name: "Center", description: "X,Y coordinates." },
      { name: "Radius", description: "Circle radius in pixels." },
      { name: "Thickness", description: "Line thickness. Negative values imply a filled circle." },
    ],
    useCases: ["Highlighting keypoints, drawing masks."],
  },
  drawingoperations_drawrectangle: {
    type: "drawingoperations_drawrectangle",
    name: "Draw Rectangle",
    description: "Draws a simple, thick, or filled up-right rectangle.",
    parameters: [
      { name: "Top-Left", description: "Starting corner coordinates." },
      { name: "Bottom-Right", description: "Opposite corner coordinates." },
    ],
    useCases: ["Creating bounding boxes for detected objects."],
  },

  // --- Blurring ---
  blurring_applyblur: {
    type: "blurring_applyblur",
    name: "Simple Blur",
    description:
      "Smoothes an image using a normalized box filter. Replaces each pixel with the average of its neighbors.",
    parameters: [{ name: "Kernel Size (KSize)", description: "Size of the averaging box." }],
    formula: "K = 1/(width * height) * [1 ... 1] matrix",
    useCases: ["Removing camera noise, softening image features."],
  },
  blurring_applygaussianblur: {
    type: "blurring_applygaussianblur",
    name: "Gaussian Blur",
    description:
      "Blurs an image using a Gaussian filter. Highly effective at removing Gaussian noise from the image.",
    parameters: [
      { name: "Kernel Size", description: "Dimensions of the kernel. Must be positive and odd." },
      { name: "SigmaX / SigmaY", description: "Gaussian kernel standard deviation in X/Y axes." },
    ],
    formula: "G(x,y) = (1/(2 * π * σ^2)) * e^(-(x^2 + y^2) / (2 * σ^2))",
    useCases: ["Preparing images for edge detection, general noise removal."],
  },
  blurring_applymedianblur: {
    type: "blurring_applymedianblur",
    name: "Median Blur",
    description:
      "Replaces each pixel's value with the median of its neighboring pixels. Highly effective against salt-and-pepper noise.",
    parameters: [
      { name: "Kernel Size", description: "Aperture linear size; must be odd and > 1." },
    ],
    useCases: ["Removing salt-and-pepper noise while preserving hard edges."],
  },

  // --- Filtering ---
  filtering_bilateral: {
    type: "filtering_bilateral",
    name: "Bilateral Filter",
    description: "A highly effective noise-reducing filter that preserves sharp edges.",
    parameters: [
      { name: "Diameter", description: "Diameter of each pixel neighborhood." },
      { name: "Sigma Color", description: "Filter sigma in the color space." },
      { name: "Sigma Space", description: "Filter sigma in the coordinate space." },
    ],
    useCases: ["Smoothing textures while keeping edges crisp (e.g., cartoonizing)."],
  },
  filtering_sharpen: {
    type: "filtering_sharpen",
    name: "Sharpen",
    description:
      "Enhances edges and high-frequency detail in an image using a custom convolution kernel.",
    parameters: [{ name: "Intensity", description: "Strength of the sharpening effect." }],
    formula: "K = [[0, -1, 0], [-1, 5, -1], [0, -1, 0]]",
    useCases: ["Enhancing blurry photos, making text more readable."],
  },
  filtering_pyramidup: {
    type: "filtering_pyramidup",
    name: "Pyramid Up",
    description:
      "Upsamples an image by injecting even zero rows/cols and applying a Gaussian filter.",
    parameters: [],
    useCases: ["Reconstructing images to double their spatial resolution."],
  },
  filtering_boxfilter: {
    type: "filtering_boxfilter",
    name: "Box Filter",
    description:
      "Blurs an image using a box filter convolution. Similar to normalized blur but can be unnormalized.",
    parameters: [
      { name: "Depth", description: "Output image depth." },
      { name: "Kernel Size", description: "Dimensions of the filter." },
    ],
    useCases: ["Fast integral image calculation, crude smoothing."],
  },
  filtering_pyramiddown: {
    type: "filtering_pyramiddown",
    name: "Pyramid Down",
    description: "Blurs an image and downsamples it by rejecting even rows and columns.",
    parameters: [],
    useCases: ["Creating image pyramids for multi-scale feature detection."],
  },
  filtering_erosion: {
    type: "filtering_erosion",
    name: "Erosion",
    description:
      "Erodes away the boundaries of foreground object. The pixel in the original image will be considered 1 only if all the pixels under the kernel is 1.",
    parameters: [{ name: "Iterations", description: "Number of times erosion is applied." }],
    useCases: ["Removing small white noises, detaching two connected objects."],
  },
  filtering_dilation: {
    type: "filtering_dilation",
    name: "Dilation",
    description:
      "Increases the white region in the image or size of foreground object. Opposite of erosion.",
    parameters: [{ name: "Iterations", description: "Number of times dilation is applied." }],
    useCases: ["Joining broken parts of an object, accentuating features."],
  },
  filtering_morphological: {
    type: "filtering_morphological",
    name: "Morphological Ops",
    description:
      "Advanced morphological operations like Opening (erosion followed by dilation) and Closing (dilation followed by erosion).",
    parameters: [
      { name: "Operation Type", description: "Morp API enum (e.g., OPEN, CLOSE, GRADIENT)." },
    ],
    useCases: ["Removing inner object noise, finding outlines."],
  },

  // --- Thresholding ---
  thresholding_adaptivethreshold: {
    type: "thresholding_adaptivethreshold",
    name: "Adaptive Threshold",
    description:
      "Calculates the threshold for small regions of the image, getting better results for varying lighting conditions.",
    parameters: [
      { name: "Max Value", description: "Value assigned to pixels passing the threshold." },
      { name: "Method", description: "Mean or Gaussian adaptive algorithm." },
      { name: "Block Size", description: "Size of the pixel neighborhood used." },
    ],
    useCases: ["Reading text over shadows, document OCR."],
  },
  thresholding_applythreshold: {
    type: "thresholding_applythreshold",
    name: "Apply Threshold",
    description: "Applies a fixed-level threshold to every pixel.",
    parameters: [
      { name: "Threshold Value", description: "Comparison baseline pixel value." },
      { name: "Threshold Type", description: "Truncate, To Zero, Binary, etc." },
    ],
    useCases: ["Creating masks directly from uniform lighting conditions."],
  },
  thresholding_applyborders: {
    type: "thresholding_applyborders",
    name: "Apply Borders",
    description: "Forms a padded image border.",
    parameters: [
      {
        name: "Border Type",
        description:
          "Border extrapolation method: Constant (fixed value), Replicate (edge pixels repeated), Reflect (mirrored), Wrap (tiled).",
      },
    ],
    useCases: ["Padding images before convolution to preserve boundary pixels."],
  },
  border_for_all: {
    type: "border_for_all",
    name: "Border (All Sides)",
    description: "Applies a uniform border thickness to all four sides of the image.",
    parameters: [
      { name: "Border Width", description: "Thickness of the border in pixels." },
      {
        name: "Border Type",
        description:
          "Border extrapolation method: Constant (fixed value), Replicate (edge pixels repeated), Reflect (mirrored), Wrap (tiled).",
      },
      { name: "Value", description: "Color of the border if constant type." },
    ],
    useCases: [
      "Standardizing input size for ML models.",
      "Creating decorative frames for display.",
      "Padding an image proportionally before applying a large kernel convolution to prevent data loss.",
    ],
  },
  border_each_side: {
    type: "border_each_side",
    name: "Border (Each Side)",
    description:
      "Applies a configurable border thickness independently to top, bottom, left, and right sides.",
    parameters: [
      { name: "Top", description: "Thickness of the top border." },
      { name: "Bottom", description: "Thickness of the bottom border." },
      { name: "Left", description: "Thickness of the left border." },
      { name: "Right", description: "Thickness of the right border." },
      {
        name: "Border Type",
        description:
          "Border extrapolation method: Constant (fixed value), Replicate (edge pixels repeated), Reflect (mirrored), Wrap (tiled).",
      },
      { name: "Value", description: "Color of the border if constant type." },
    ],
    useCases: [
      "Asymmetric padding to center an off-center subject.",
      "Letterboxing an image to fit a specific aspect ratio without distorting pixels.",
    ],
  },
  thresholding_otsuthreshold: {
    type: "thresholding_otsuthreshold",
    name: "Otsu's Thresholding",
    description:
      "Automatically calculates an optimal threshold value by analyzing the image histogram to minimize intra-class variance.",
    parameters: [],
    useCases: [
      "Bimodal images where foreground and background pixel distributions are well separated.",
    ],
  },

  // --- Sobel Derivatives ---
  sobelderivatives_soblederivate: {
    type: "sobelderivatives_soblederivate",
    name: "Sobel Operator",
    description:
      "Calculates the first, second, third, or mixed image derivatives using an extended Sobel operator.",
    parameters: [
      { name: "DX, DY", description: "Order of the derivative x and y." },
      { name: "KSize", description: "Size of the extended Sobel kernel (must be 1, 3, 5, or 7)." },
    ],
    formula: "G = √(Gx² + Gy²)",
    useCases: ["Edge detection, finding intensity gradients."],
  },
  sobelderivatives_scharrderivate: {
    type: "sobelderivatives_scharrderivate",
    name: "Scharr Operator",
    description:
      "Calculates the first spatial image derivative using the Scharr filter instead of Sobel for better rotational symmetry.",
    parameters: [
      {
        name: "DX, DY",
        description: "Order of the derivative in x and y (only one can be 1, the other 0).",
      },
    ],
    formula: "Gx = [[-3, 0, 3], [-10, 0, 10], [-3, 0, 3]]",
    useCases: ["Accurate gradient direction computation."],
  },

  // --- Transformation ---
  transformation_distance: {
    type: "transformation_distance",
    name: "Distance Transform",
    description:
      "Calculates the distance to the closest zero pixel for each pixel of the source image.",
    parameters: [
      { name: "Distance Type", description: "L1, L2 (Euclidean), or C (Chebyshev) metrics." },
      { name: "Mask Size", description: "3x3, 5x5, or precise calculation methods." },
    ],
    useCases: ["Watershed segmentation, finding the skeleton of shapes."],
  },
  transformation_laplacian: {
    type: "transformation_laplacian",
    name: "Laplacian Operator",
    description:
      "Calculates the Laplacian of an image, highlighting regions of rapid intensity change.",
    parameters: [
      {
        name: "KSize",
        description: "Aperture size used to compute the second-derivative filters.",
      },
    ],
    formula: "Δf = ∂²f/∂x² + ∂²f/∂y²",
    useCases: ["Blob detection, sharpening edge transitions."],
  },
};
