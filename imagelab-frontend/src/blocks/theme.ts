import * as Blockly from "blockly";

export const imagelabTheme = Blockly.Theme.defineTheme("imagelab", {
  name: "imagelab",
  base: Blockly.Themes.Zelos,
  blockStyles: {
    basic_style: {
      colourPrimary: "#81C784",
      colourSecondary: "#66BB6A",
      colourTertiary: "#4CAF50",
    },
    geometric_style: {
      colourPrimary: "#64B5F6",
      colourSecondary: "#42A5F5",
      colourTertiary: "#2196F3",
    },
    conversions_style: {
      colourPrimary: "#FF8A65",
      colourSecondary: "#FF7043",
      colourTertiary: "#FF5722",
    },
    drawing_style: {
      colourPrimary: "#BA68C8",
      colourSecondary: "#AB47BC",
      colourTertiary: "#9C27B0",
    },
    blurring_style: {
      colourPrimary: "#FFB74D",
      colourSecondary: "#FFA726",
      colourTertiary: "#FF9800",
    },
    filtering_style: {
      colourPrimary: "#F06292",
      colourSecondary: "#EC407A",
      colourTertiary: "#E91E63",
    },
    thresholding_style: {
      colourPrimary: "#A1887F",
      colourSecondary: "#8D6E63",
      colourTertiary: "#795548",
    },
    sobel_derivatives_style: {
      colourPrimary: "#E57373",
      colourSecondary: "#EF5350",
      colourTertiary: "#F44336",
    },
    transformation_style: {
      colourPrimary: "#4DB6AC",
      colourSecondary: "#26A69A",
      colourTertiary: "#009688",
    },
  },
  componentStyles: {
    workspaceBackgroundColour: "#F9FAFB",
    scrollbarColour: "#D1D5DB",
    insertionMarkerColour: "#6366F1",
  },
  fontStyle: {
    family: "Inter Variable, system-ui, sans-serif",
    weight: "500",
    size: 11,
  },
});
