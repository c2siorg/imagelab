export const augmentationBlocks = [
  {
    type: "augmentation_gaussiannoise",
    message0: "Add Gaussian Noise %1 Mean %2 %3 Sigma %4",
    args0: [
      { type: "input_dummy" },
      { type: "field_number", name: "mean", value: 0, min: -127, max: 127 },
      { type: "input_dummy" },
      { type: "field_number", name: "sigma", value: 25, min: 1, max: 255 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "augmentation_style",
    tooltip:
      "Adds Gaussian noise to the image - Simulates random sensor noise by adding values sampled from a Gaussian (normal) distribution to each pixel. The mean controls the average noise offset (0 for no bias) and sigma controls the intensity of the noise — higher sigma means more visible noise. Useful for teaching denoising techniques and understanding how noise affects image processing pipelines.",
  },
  {
    type: "augmentation_saltpeppernoise",
    message0: "Add Salt & Pepper Noise %1 Density %2",
    args0: [
      { type: "input_dummy" },
      {
        type: "field_number",
        name: "density",
        value: 0.05,
        min: 0,
        max: 1,
        precision: 0.01,
      },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "augmentation_style",
    tooltip:
      "Adds salt and pepper noise to the image - Randomly sets a proportion of pixels to either white (salt) or black (pepper), simulating corrupted pixels from transmission errors or faulty sensors. The density parameter (0–1) controls the fraction of affected pixels — for example, 0.05 means 5% of pixels are corrupted. Useful for teaching median blur as a denoising technique.",
  },
  {
    type: "augmentation_sepiafilter",
    message0: "Apply Sepia Filter %1 Intensity %2",
    args0: [
      { type: "input_dummy" },
      {
        type: "field_number",
        name: "intensity",
        value: 1.0,
        min: 0,
        max: 1,
        precision: 0.1,
      },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "augmentation_style",
    tooltip:
      "Applies a sepia filter to the image - Transforms the image using a sepia color matrix to produce a warm, brownish vintage tone. The intensity parameter (0–1) controls the strength of the effect — 0 leaves the image unchanged and 1 applies the full sepia transformation. Useful for teaching color matrix transforms and blending operations.",
  },
  {
    type: "augmentation_vignette",
    message0: "Apply Vignette Filter %1 Radius %2 %3 Intensity %4",
    args0: [
      { type: "input_dummy" },
      {
        type: "field_number",
        name: "radius",
        value: 0.8,
        min: 0.1,
        max: 2.0,
        precision: 0.05,
      },
      { type: "input_dummy" },
      {
        type: "field_number",
        name: "intensity",
        value: 0.6,
        min: 0,
        max: 1,
        precision: 0.05,
      },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "augmentation_style",
    tooltip:
      "Applies a radial vignette optical falloff effect to the image - Simulates natural camera lens shading by smoothly decreasing peripheral brightness toward the image edges using separable 2D Gaussian kernels. The radius controls the relative size of the central unshaded region (0.1 to 2.0), and intensity controls the darkening strength at the periphery (0 for unchanged to 1 for maximum darkening). Useful for photographic styling and simulating optical distortions.",
  },
  {
    type: "augmentation_motionblur",
    message0: "Apply Motion Blur %1 Kernel size %2 %3 Angle (deg) %4",
    args0: [
      { type: "input_dummy" },
      { type: "field_number", name: "kernel_size", value: 15, min: 3, max: 61 },
      { type: "input_dummy" },
      { type: "field_number", name: "angle", value: 0, min: 0, max: 360 },
    ],
    previousStatement: null,
    nextStatement: null,
    style: "augmentation_style",
    tooltip:
      "Applies directional motion blur to simulate camera movement or subject velocity along a linear path. Kernel size controls blur extent (larger = stronger blur) and angle defines the motion direction in degrees (0 = horizontal, 90 = vertical).",
  },
];
