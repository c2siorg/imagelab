/**
 * Shared test utilities for integration tests
 */
import { vi } from "vitest";
import * as Blockly from "blockly";

// Store original scrollIntoView for cleanup
const originalScrollIntoView = Element.prototype.scrollIntoView;

/**
 * Mock Element.scrollIntoView to avoid errors in components that use it
 */
export function mockScrollIntoView() {
  Element.prototype.scrollIntoView = vi.fn();
}

/**
 * Restore original scrollIntoView
 */
export function restoreScrollIntoView() {
  Element.prototype.scrollIntoView = originalScrollIntoView;
}

/**
 * Mock HTMLCanvasElement.getContext to avoid jsdom canvas requirement
 * Reuses the pattern from HistogramCanvas.test.tsx
 */
export function mockCanvasContext() {
  const mockCanvasContext: Partial<CanvasRenderingContext2D> = {
    scale: vi.fn(),
    clearRect: vi.fn(),
    fillStyle: "",
    fillRect: vi.fn(),
    strokeStyle: "",
    lineWidth: 1,
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    stroke: vi.fn(),
  };

  HTMLCanvasElement.prototype.getContext = vi.fn(
    () => mockCanvasContext as CanvasRenderingContext2D,
  ) as unknown as typeof HTMLCanvasElement.prototype.getContext;

  return mockCanvasContext;
}

/**
 * Create a minimal mock Blockly block for testing
 */
export function createMockBlock(id: string, type: string): Partial<Blockly.Block> {
  return {
    id,
    type,
    select: vi.fn(),
    getFieldValue: vi.fn(() => null),
  } as unknown as Blockly.Block;
}

/**
 * Create a minimal mock Blockly workspace for testing
 */
export function createMockWorkspace(): Partial<Blockly.WorkspaceSvg> {
  const blocks = new Map<string, Partial<Blockly.Block>>();

  return {
    getBlockById: vi.fn((id: string) => {
      const block = blocks.get(id);
      return (block as unknown as Blockly.BlockSvg) ?? null;
    }) as unknown as (id: string) => Blockly.BlockSvg | null,
    addChangeListener: vi.fn(),
    removeChangeListener: vi.fn(),
    clear: vi.fn(),
    undo: vi.fn(),
    centerOnBlock: vi.fn(),
  };
}

/**
 * Reset all mocks and clean up store state
 */
export function cleanupMocks() {
  vi.clearAllMocks();
  vi.restoreAllMocks();
}
