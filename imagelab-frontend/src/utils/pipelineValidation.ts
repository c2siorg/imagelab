import type { PipelineStep } from "../types/pipeline";

export interface ValidationWarning {
  step: number;
  operatorType: string;
  message: string;
}

// Operators that require a grayscale (single-channel) input
const REQUIRES_GRAYSCALE = new Set([
  "imageconvertions_graytobinary",
  "thresholding_applythreshold",
  "thresholding_adaptivethreshold",
  "thresholding_otsuthreshold",
  "transformation_distance",
]);

// Operators that require a colour (3-channel BGR) input
const REQUIRES_COLOR = new Set([
  "imageconvertions_bgrtohsv",
  "imageconvertions_bgrtolab",
  "imageconvertions_bgrtoycrcb",
  "imageconvertions_colortobinary",
  "segmentation_watershed",
  "segmentation_kmeans",
  "segmentation_meanshift",
]);

// Operators that output grayscale
const OUTPUTS_GRAYSCALE = new Set([
  "imageconvertions_grayimage",
  "imageconvertions_graytobinary",
  "imageconvertions_colortobinary",
  "imageconvertions_channelsplit",
  "thresholding_applythreshold",
  "thresholding_adaptivethreshold",
  "thresholding_otsuthreshold",
  "transformation_distance",
  "sobelderivatives_soblederivate",
  "sobelderivatives_scharrderivate",
  "sobelderivatives_robertscross",
  "filtering_cannyedge",
]);

// Operators that output colour
const OUTPUTS_COLOR = new Set([
  "basic_readimage",
  "imageconvertions_clahe",
  "imageconvertions_colormaps",
  "imageconvertions_hsvtobgr",
  "imageconvertions_labtobgr",
  "imageconvertions_ycrcbtobgr",
  "segmentation_watershed",
  "segmentation_kmeans",
  "segmentation_meanshift",
]);

type ChannelState = "color" | "grayscale" | "unknown";

function friendlyName(operatorType: string): string {
  const suffix = operatorType.includes("_")
    ? operatorType.split("_").slice(1).join(" ")
    : operatorType;
  return suffix.replace(/([a-z])([A-Z])/g, "$1 $2");
}

export function validatePipeline(pipeline: PipelineStep[]): ValidationWarning[] {
  const warnings: ValidationWarning[] = [];
  let channelState: ChannelState = "unknown";

  pipeline.forEach((step, index) => {
    const stepNumber = index + 1;
    const type = step.type;

    // Skip read/write blocks from channel incompatibility checks
    if (type === "basic_readimage") {
      channelState = "color";
      return;
    }
    if (type === "basic_writeimage") return;

    // Check incompatibilities based on current channel state
    if (channelState === "grayscale" && REQUIRES_COLOR.has(type)) {
      warnings.push({
        step: stepNumber,
        operatorType: type,
        message: `"${friendlyName(type)}" expects a colour image but the previous step outputs grayscale. This will likely cause an error at runtime.`,
      });
    }

    if (channelState === "color" && REQUIRES_GRAYSCALE.has(type)) {
      warnings.push({
        step: stepNumber,
        operatorType: type,
        message: `"${friendlyName(type)}" expects a grayscale image but the previous step outputs colour. Add a Gray Image block before this step.`,
      });
    }

    // Update channel state based on this step's output
    if (OUTPUTS_GRAYSCALE.has(type)) {
      channelState = "grayscale";
    } else if (OUTPUTS_COLOR.has(type)) {
      channelState = "color";
    }
  });

  // Warn if pipeline has no Read Image block
  const hasReadImage = pipeline.some((s) => s.type === "basic_readimage");
  if (!hasReadImage) {
    warnings.push({
      step: 0,
      operatorType: "basic_readimage",
      message: 'No "Read Image" block found. The pipeline will not execute.',
    });
  }

  // Warn if pipeline has no Write Image block
  const hasWriteImage = pipeline.some((s) => s.type === "basic_writeimage");
  if (!hasWriteImage) {
    warnings.push({
      step: pipeline.length,
      operatorType: "basic_writeimage",
      message: 'No "Write Image" block found. The processed image will not be saved to disk.',
    });
  }

  return warnings;
}
