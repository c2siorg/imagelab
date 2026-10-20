---
layout: page
title: Applications
---

This page helps you to take the headstart to play with ImageLab. This includes prominent image processing applications you can create under this version of the project.

## 1. Image Pyramids Up and Down

Pyramid is an operation on an image where,

An input image is initially smoothed using a particular smoothing filter (ex: Gaussian, Laplacian) and then the smoothed image is subsampled.

This process is repeated multiple times.

During the pyramid operation, the smoothness of the image is increased and the resolution (size) is decreased.

There are two variation of image pyramids. That are Pyramids Up & Down.

`Pyramids Up` - This operation will initially up sampled and then blurred the image

`Pyramids Down` - This operation will initailly blurred and then down sampled

![Image pyramids](./../assets/image_pyramids.gif)

As in the above demo, it clearly visible that by a one iteration of pyramids up and down will reduce the image quality. It means that the operator has downgrade the image qualities.

## 2. Image Analysis with Histograms

Histograms is a graph or plot, which gives you an abtract idea about the intensity distribution of an image. It is a plot with pixel values(0-255) in X-axis and corresponding of number of pixels in the image on Y-axis.

You can apply histogram operator from the `Histogram Operations` operator section and make sure that to apply the operator at the end of the pipeline to clearly demostrate the chnages occuring when properties changed on each operator.

Application automatically detect whether the image is a RGB or Gray image.Based upon that it will output the histogram.

### RGB Histogram

![RGB Image](./../assets/rgb-histogram.gif)

### Gray image Histogram

![Gray Image](./../assets/gray-histogram.gif)

<br>

## 3. Find & Draw the Contours in an image

This operation despite to use contours for a particular image. in order to use contours, move to `Contour Operations` in the sidebar and drag and drop the `FIND-CONTOURS` operator to the stream. Before applying this operator we need to pre-process with image conversion(RGB-to-Gray) and Image blurring(Smoothing)

![Find Contours](./../assets/find-contours.gif)

Contours can be explained simply as a curve joining all the continuous points (along the boundary), having same color or intensity. The contours are a useful tool for shape analysis and object detection and recognition.

To get accurate results we need to use a binary image. So before finding contours, apply thresold or canny edge detection.

<br>

## 4. Interactive Region of Interest (ROI) & Visual Canvas Inspection

ImageLab includes interactive canvas overlay tools directly in the preview pane, allowing you to visually crop regions, compare execution stages, and inspect pixel-level metrics without leaving the workflow:

### Interactive ROI Selection & Block Synchronization

When tuning operations like `Crop Image` or `Draw Rectangle`, guessing $(x, y, w, h)$ pixel coordinates manually is tedious and error-prone. The docked **ROI Tool** provides an interactive canvas overlay:

- **Freeform & Constrained Aspect Ratios**: Draw bounding boxes freely or lock aspect ratios (`1:1`, `4:3`, `16:9`) for standard framing.
- **Corner & Edge Transform Handles**: Scale, move, and reposition the bounding box across full-resolution image coordinate space.
- **Statistical HUD**: Live floating overlay showing ROI dimensions (`W × H px`), origin `(X, Y)`, mean intensity ($\mu$), and standard deviation ($\sigma$).
- **One-Click Sync**: Click **Apply to Block** to transfer exact coordinates directly into the selected `geometric_cropimage` or `drawingoperations_drawrectangle` block in the Blockly workspace.
- **Clipboard Export**: Copy the bounding box coordinates directly with **Copy**.

![ROI Crop Selection](./../assets/roi_crop_selection_preview.png)

### Before / After Step Comparison Slider

Compare the input or any previous pipeline step with your current output:

- **Split Mode**: Interactive vertical wipe divider allowing side-by-side before/after comparison.
- **Diff Mode**: Absolute difference heatmap highlighting exact pixel alterations introduced by the operator.
- **Hold Mode**: Press-and-hold instant toggle between original and processed frames for rapid visual blink tests.
- **Colormap & Fullscreen**: Inspect subtle contrast shifts with perceptual pseudocolor maps or view comparisons in fullscreen.

### Sub-Pixel Inspector & Neighborhood Loupe

Hover over any region of the preview to examine high-precision pixel data:

- **Magnified Loupe**: Displays a $5 \times 5$ pixel neighborhood grid centered around the cursor with contrasting boundary rings.
- **Quantitative Metrics**: Instant readout of RGB channel values, ITU-R BT.601 perceptual luminance, and normalized coordinates.
