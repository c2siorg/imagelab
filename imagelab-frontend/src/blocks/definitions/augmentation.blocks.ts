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
];
