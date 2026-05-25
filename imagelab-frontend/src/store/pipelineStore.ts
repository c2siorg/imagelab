import { create } from "zustand";
import * as Blockly from "blockly";
import { categories } from "../blocks/categories";
import { clearPersistedImage, saveImageState } from "../hooks/imagePersistence";
const imageResetListeners = new Set<() => void>();
const imageLabelSyncListeners = new Set<(filename: string | null) => void>();
import type { ImageAnalysis, PipelineTimings, StepResult } from "../types/pipeline";

interface PipelineState {
  originalImage: string | null;
  imageFormat: string;
  imageFilename: string | null;
  processedImage: string | null;
  executionId: string | null;
  stepResults: StepResult[];
  activeStepBlockId: string | null;
  activeStepIndex: number | null;
  activeStepAnalysis: ImageAnalysis | null;
  isInspectingStep: boolean;
  isExecuting: boolean;
  error: string | null;
  errorStep: number | null;
  selectedBlockType: string | null;
  selectedBlockTooltip: string | null;
  timings: PipelineTimings | null;
  isCameraModalOpen: boolean;
  cameraCaptureHandler:
    | ((payload: { image: string; format: string; label: string }) => void)
    | null;

  // Statistics
  blockCount: number;
  uniqueBlockTypes: number;
  categoryCounts: Record<string, number>;
  complexity: "Low" | "Medium" | "High";
  setOriginalImage: (image: string, format: string, filename?: string | null) => void;
  setProcessedImage: (image: string | null) => void;
  setPreviewImage: (image: string | null) => void;
  setExecutionId: (executionId: string | null) => void;
  setStepResults: (results: StepResult[]) => void;
  setActiveStep: (blockId: string | null, index?: number | null) => void;
  setActiveStepAnalysis: (analysis: ImageAnalysis | null) => void;
  setInspectingStep: (inspecting: boolean) => void;
  setExecuting: (executing: boolean) => void;
  setError: (error: string | null, step?: number | null) => void;
  setSelectedBlock: (type: string | null, tooltip: string | null) => void;
  setTiming: (timings: PipelineTimings | null) => void;
  openCameraModal: (
    onCapture: (payload: { image: string; format: string; label: string }) => void,
  ) => void;
  closeCameraModal: () => void;
  updateBlockStats: (workspace: Blockly.WorkspaceSvg) => void;
  reset: () => void;
  clearImage: () => void;
  registerImageReset: (fn: () => void) => () => void;
  registerImageLabelSync: (fn: (filename: string | null) => void) => () => void;
}

function calculateComplexity(blocks: number, unique: number): "Low" | "Medium" | "High" {
  if (blocks === 0) return "Low";
  if (blocks > 10 || unique > 5) return "High";
  if (blocks > 3 || unique > 2) return "Medium";
  return "Low";
}

export const usePipelineStore = create<PipelineState>((set) => ({
  originalImage: null,
  imageFormat: "png",
  imageFilename: null,
  processedImage: null,
  executionId: null,
  stepResults: [],
  activeStepBlockId: null,
  activeStepIndex: null,
  activeStepAnalysis: null,
  isInspectingStep: false,
  isExecuting: false,
  error: null,
  errorStep: null,
  selectedBlockType: null,
  selectedBlockTooltip: null,
  timings: null,
  isCameraModalOpen: false,
  cameraCaptureHandler: null,
  blockCount: 0,
  uniqueBlockTypes: 0,
  categoryCounts: {},
  complexity: "Low",
  setOriginalImage: (image, format, filename = null) => {
    imageLabelSyncListeners.forEach((listener) => listener(filename));
    saveImageState({ image, format, filename });
    set({
      originalImage: image,
      imageFormat: format,
      imageFilename: filename,
      processedImage: null,
      executionId: null,
      stepResults: [],
      activeStepBlockId: null,
      activeStepIndex: null,
      activeStepAnalysis: null,
      error: null,
      timings: null,
    });
  },
  setProcessedImage: (image) => set({ processedImage: image, error: null, errorStep: null }),
  setPreviewImage: (image) => set({ processedImage: image }),
  setExecutionId: (executionId) => set({ executionId }),
  setStepResults: (results) => set({ stepResults: results }),
  setActiveStep: (blockId, index = null) =>
    set({ activeStepBlockId: blockId, activeStepIndex: index }),
  setActiveStepAnalysis: (analysis) => set({ activeStepAnalysis: analysis }),
  setInspectingStep: (inspecting) => set({ isInspectingStep: inspecting }),
  setExecuting: (executing) => set({ isExecuting: executing }),
  setError: (error, step = null) => set({ error, errorStep: step }),
  setSelectedBlock: (type, tooltip) =>
    set({ selectedBlockType: type, selectedBlockTooltip: tooltip }),
  setTiming: (timings) => set({ timings }),
  openCameraModal: (onCapture) =>
    set({
      isCameraModalOpen: true,
      cameraCaptureHandler: onCapture,
    }),
  closeCameraModal: () =>
    set({
      isCameraModalOpen: false,
      cameraCaptureHandler: null,
    }),
  registerImageReset: (fn) => {
    imageResetListeners.add(fn);
    return () => {
      imageResetListeners.delete(fn);
    };
  },
  registerImageLabelSync: (fn) => {
    imageLabelSyncListeners.add(fn);
    return () => {
      imageLabelSyncListeners.delete(fn);
    };
  },
  clearImage: () => {
    imageResetListeners.forEach((listener) => listener());
    imageLabelSyncListeners.forEach((listener) => listener(null));
    clearPersistedImage();
    set({
      originalImage: null,
      imageFormat: "png",
      imageFilename: null,
      processedImage: null,
      executionId: null,
      stepResults: [],
      activeStepBlockId: null,
      activeStepIndex: null,
      activeStepAnalysis: null,
      isInspectingStep: false,
      error: null,
      errorStep: null,
      timings: null,
      isCameraModalOpen: false,
      cameraCaptureHandler: null,
    });
  },
  updateBlockStats: (workspace) => {
    const blocks = workspace.getAllBlocks(false);

    const typeToCategory: Record<string, string> = {};
    categories.forEach((cat) => {
      cat.blocks.forEach((b) => {
        typeToCategory[b.type] = cat.name;
      });
    });

    const uniqueTypes = new Set<string>();
    const counts: Record<string, number> = {};

    blocks.forEach((block) => {
      uniqueTypes.add(block.type);
      const cat = typeToCategory[block.type] || "Unknown";
      counts[cat] = (counts[cat] || 0) + 1;
    });

    set({
      blockCount: blocks.length,
      uniqueBlockTypes: uniqueTypes.size,
      categoryCounts: counts,
      complexity: calculateComplexity(blocks.length, uniqueTypes.size),
    });
  },
  reset: () => {
    imageResetListeners.forEach((listener) => listener());
    imageLabelSyncListeners.forEach((listener) => listener(null));
    imageResetListeners.clear();
    imageLabelSyncListeners.clear();
    clearPersistedImage();
    set({
      originalImage: null,
      imageFormat: "png",
      imageFilename: null,
      processedImage: null,
      executionId: null,
      stepResults: [],
      activeStepBlockId: null,
      activeStepIndex: null,
      activeStepAnalysis: null,
      isInspectingStep: false,
      isExecuting: false,
      error: null,
      errorStep: null,
      selectedBlockType: null,
      selectedBlockTooltip: null,
      blockCount: 0,
      uniqueBlockTypes: 0,
      categoryCounts: {},
      complexity: "Low",
      timings: null,
      isCameraModalOpen: false,
      cameraCaptureHandler: null,
    });
  },
}));
