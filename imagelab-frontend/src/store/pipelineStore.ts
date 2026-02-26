import { create } from 'zustand';
import * as Blockly from 'blockly';
import { categories } from '../blocks/categories';

interface PipelineState {
  originalImage: string | null;
  imageFormat: string;
  processedImage: string | null;
  isExecuting: boolean;
  error: string | null;
  errorStep: number | null;
  selectedBlockType: string | null;
  selectedBlockTooltip: string | null;

  // Statistics
  blockCount: number;
  uniqueBlockTypes: number;
  categoryCounts: Record<string, number>;
  complexity: 'Low' | 'Medium' | 'High';
  setOriginalImage: (image: string, format: string) => void;
  setProcessedImage: (image: string | null) => void;
  setExecuting: (executing: boolean) => void;
  setError: (error: string | null, step?: number | null) => void;
  setSelectedBlock: (type: string | null, tooltip: string | null) => void;
  updateBlockStats: (workspace: Blockly.WorkspaceSvg) => void;
  reset: () => void;
  clearImage: () => void;
  _imageResetFn: (() => void) | null;
  registerImageReset: (fn: () => void) => void;
}

function calculateComplexity(blocks: number, unique: number): 'Low' | 'Medium' | 'High' {
  if (blocks === 0) return 'Low';
  if (blocks > 10 || unique > 5) return 'High';
  if (blocks > 3 || unique > 2) return 'Medium';
  return 'Low';
}

export const usePipelineStore = create<PipelineState>((set) => ({
  originalImage: null,
  imageFormat: 'png',
  processedImage: null,
  isExecuting: false,
  error: null,
  errorStep: null,
  selectedBlockType: null,
  selectedBlockTooltip: null,
  blockCount: 0,
  uniqueBlockTypes: 0,
  categoryCounts: {},
  complexity: 'Low',
  setOriginalImage: (image, format) => set({ originalImage: image, imageFormat: format, processedImage: null, error: null }),
  setProcessedImage: (image) => set({ processedImage: image, error: null, errorStep: null }),
  setExecuting: (executing) => set({ isExecuting: executing }),
  setError: (error, step = null) => set({ error, errorStep: step }),
  setSelectedBlock: (type, tooltip) => set({ selectedBlockType: type, selectedBlockTooltip: tooltip }),
  _imageResetFn: null as (() => void) | null,
  registerImageReset: (fn) => set({ _imageResetFn: fn }),
  clearImage: () => {
    const state = usePipelineStore.getState();
    if (state._imageResetFn) state._imageResetFn();
    set({ originalImage: null, processedImage: null, error: null, errorStep: null });
  },
  updateBlockStats: (workspace) => {
    const blocks = workspace.getAllBlocks(false);

    const typeToCategory: Record<string, string> = {};
    categories.forEach(cat => {
      cat.blocks.forEach(b => {
        typeToCategory[b.type] = cat.name;
      });
    });

    const uniqueTypes = new Set<string>();
    const counts: Record<string, number> = {};

    blocks.forEach(block => {
      uniqueTypes.add(block.type);
      const cat = typeToCategory[block.type] || 'Unknown';
      counts[cat] = (counts[cat] || 0) + 1;
    });

    set({
      blockCount: blocks.length,
      uniqueBlockTypes: uniqueTypes.size,
      categoryCounts: counts,
      complexity: calculateComplexity(blocks.length, uniqueTypes.size)
    });
  },
  reset: () => set({
    originalImage: null,
    imageFormat: 'png',
    processedImage: null,
    isExecuting: false,
    error: null,
    errorStep: null,
    selectedBlockType: null,
    selectedBlockTooltip: null,
    blockCount: 0,
    uniqueBlockTypes: 0,
    categoryCounts: {},
    complexity: 'Low'
  }),
}));
