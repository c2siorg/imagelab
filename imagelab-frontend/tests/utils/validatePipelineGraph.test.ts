/**
 * @vitest-environment jsdom
 */
import { describe, expect, it } from "vitest";
import { validatePipelineGraph } from "../../src/utils/validatePipelineGraph";
import type { PipelineGraph } from "../../src/types/macro";

describe("validatePipelineGraph", () => {
  describe("empty and valid pipelines", () => {
    it("returns valid for an empty graph", () => {
      const graph: PipelineGraph = { nodes: [], edges: [] };
      const result = validatePipelineGraph(graph);
      expect(result.valid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });

    it("returns valid for a simple pipeline with Read Image", () => {
      const graph: PipelineGraph = {
        nodes: [
          { id: "1", type: "basic_input", op: "basic_input", params: {} },
          { id: "2", type: "filtering_blur", op: "filtering_blur", params: {} },
        ],
        edges: [{ from: "1", to: "2" }],
      };
      const result = validatePipelineGraph(graph);
      expect(result.valid).toBe(true);
      expect(result.warnings).toHaveLength(0);
      expect(result.hasReadImage).toBe(true);
    });

    it("identifies Read Image block by various type names", () => {
      const types = ["basic_input", "readimage", "read_image"];
      
      types.forEach((type) => {
        const graph: PipelineGraph = {
          nodes: [{ id: "1", type, op: type, params: {} }],
          edges: [],
        };
        const result = validatePipelineGraph(graph);
        expect(result.hasReadImage).toBe(true);
      });
    });
  });

  describe("missing Read Image block", () => {
    it("warns when no Read Image block is present", () => {
      const graph: PipelineGraph = {
        nodes: [
          { id: "1", type: "filtering_blur", op: "filtering_blur", params: {} },
          { id: "2", type: "imageconvertions_grayimage", op: "imageconvertions_grayimage", params: {} },
        ],
        edges: [{ from: "1", to: "2" }],
      };
      const result = validatePipelineGraph(graph);
      expect(result.valid).toBe(false);
      expect(result.hasReadImage).toBe(false);
      expect(result.warnings).toHaveLength(1);
      expect(result.warnings[0].message).toContain("No \"Read Image\" block found");
    });
  });

  describe("channel type mismatches", () => {
    it("detects grayscale output feeding into color-only operator", () => {
      const graph: PipelineGraph = {
        nodes: [
          { id: "1", type: "basic_input", op: "basic_input", params: {} },
          { id: "2", type: "imageconvertions_grayimage", op: "imageconvertions_grayimage", params: {} },
          { id: "3", type: "imageconvertions_bgrtohsv", op: "imageconvertions_bgrtohsv", params: {} },
        ],
        edges: [
          { from: "1", to: "2" },
          { from: "2", to: "3" },
        ],
      };
      const result = validatePipelineGraph(graph, 3);
      expect(result.valid).toBe(false);
      expect(result.warnings.length).toBeGreaterThan(0);
      
      const channelWarning = result.warnings.find((w) => w.nodeId === "3");
      expect(channelWarning).toBeDefined();
      expect(channelWarning?.message).toContain("grayscale");
      expect(channelWarning?.message).toContain("color");
    });

    it("detects color output feeding into grayscale-only operator", () => {
      const graph: PipelineGraph = {
        nodes: [
          { id: "1", type: "basic_input", op: "basic_input", params: {} },
          { id: "2", type: "thresholding_adaptivethreshold", op: "thresholding_adaptivethreshold", params: {} },
        ],
        edges: [{ from: "1", to: "2" }],
      };
      const result = validatePipelineGraph(graph, 3); // Color input (3 channels)
      expect(result.valid).toBe(false);
      expect(result.warnings.length).toBeGreaterThan(0);
      
      const channelWarning = result.warnings.find((w) => w.nodeId === "2");
      expect(channelWarning).toBeDefined();
      expect(channelWarning?.message).toContain("grayscale");
    });

    it("accepts grayscale input for grayscale-only operators", () => {
      const graph: PipelineGraph = {
        nodes: [
          { id: "1", type: "basic_input", op: "basic_input", params: {} },
          { id: "2", type: "imageconvertions_grayimage", op: "imageconvertions_grayimage", params: {} },
          { id: "3", type: "thresholding_adaptivethreshold", op: "thresholding_adaptivethreshold", params: {} },
        ],
        edges: [
          { from: "1", to: "2" },
          { from: "2", to: "3" },
        ],
      };
      const result = validatePipelineGraph(graph, 3);
      expect(result.valid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });

    it("accepts color input for color operators", () => {
      const graph: PipelineGraph = {
        nodes: [
          { id: "1", type: "basic_input", op: "basic_input", params: {} },
          { id: "2", type: "imageconvertions_bgrtohsv", op: "imageconvertions_bgrtohsv", params: {} },
          { id: "3", type: "imageconvertions_hsvtobgr", op: "imageconvertions_hsvtobgr", params: {} },
        ],
        edges: [
          { from: "1", to: "2" },
          { from: "2", to: "3" },
        ],
      };
      const result = validatePipelineGraph(graph, 3);
      expect(result.valid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });
  });

  describe("control flow branch validation", () => {
    it("validates macro_blend requires left and right branches", () => {
      const graph: PipelineGraph = {
        nodes: [
          {
            id: "1",
            type: "macro_blend",
            op: "macro_blend",
            params: {},
            branches: {
              left: { nodes: [], edges: [] },
              // Missing right branch
            },
          },
        ],
        edges: [],
      };
      const result = validatePipelineGraph(graph);
      expect(result.valid).toBe(false);
      expect(result.warnings.length).toBeGreaterThan(0);
      
      const branchWarning = result.warnings.find((w) => w.nodeId === "1");
      expect(branchWarning).toBeDefined();
      expect(branchWarning?.message).toContain("branch");
    });

    it("validates macro_if_else requires then and else branches", () => {
      const graph: PipelineGraph = {
        nodes: [
          {
            id: "1",
            type: "macro_if_else",
            op: "macro_if_else",
            params: {},
            branches: {
              then: { nodes: [], edges: [] },
              // Missing else branch
            },
          },
        ],
        edges: [],
      };
      const result = validatePipelineGraph(graph);
      expect(result.valid).toBe(false);
      
      const branchWarning = result.warnings.find((w) => w.nodeId === "1");
      expect(branchWarning).toBeDefined();
      expect(branchWarning?.message).toContain("branch");
    });

    it("accepts control flow with correct branches", () => {
      const graph: PipelineGraph = {
        nodes: [
          { id: "0", type: "basic_input", op: "basic_input", params: {} },
          {
            id: "1",
            type: "macro_blend",
            op: "macro_blend",
            params: {},
            branches: {
              left: { nodes: [], edges: [] },
              right: { nodes: [], edges: [] },
            },
          },
        ],
        edges: [{ from: "0", to: "1" }],
      };
      const result = validatePipelineGraph(graph);
      expect(result.valid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });
  });

  describe("complex pipelines", () => {
    it("validates a multi-step pipeline with mixed channel types", () => {
      const graph: PipelineGraph = {
        nodes: [
          { id: "1", type: "basic_input", op: "basic_input", params: {} },
          { id: "2", type: "filtering_blur", op: "filtering_blur", params: {} },
          { id: "3", type: "imageconvertions_grayimage", op: "imageconvertions_grayimage", params: {} },
          { id: "4", type: "thresholding_applythreshold", op: "thresholding_applythreshold", params: {} },
        ],
        edges: [
          { from: "1", to: "2" },
          { from: "2", to: "3" },
          { from: "3", to: "4" },
        ],
      };
      const result = validatePipelineGraph(graph, 3);
      expect(result.valid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });

    it("detects multiple validation issues in one pipeline", () => {
      const graph: PipelineGraph = {
        nodes: [
          // No Read Image block
          { id: "1", type: "filtering_blur", op: "filtering_blur", params: {} },
          { id: "2", type: "imageconvertions_grayimage", op: "imageconvertions_grayimage", params: {} },
          // Color-only operator after grayscale
          { id: "3", type: "imageconvertions_bgrtohsv", op: "imageconvertions_bgrtohsv", params: {} },
        ],
        edges: [
          { from: "1", to: "2" },
          { from: "2", to: "3" },
        ],
      };
      const result = validatePipelineGraph(graph, 3);
      expect(result.valid).toBe(false);
      expect(result.warnings.length).toBeGreaterThanOrEqual(2);
      expect(result.hasReadImage).toBe(false);
    });
  });

  describe("port-specific validation", () => {
    it("validates merge_images with correct mask port", () => {
      const graph: PipelineGraph = {
        nodes: [
          { id: "1", type: "basic_input", op: "basic_input", params: {} },
          { id: "2", type: "imageconvertions_grayimage", op: "imageconvertions_grayimage", params: {} },
          { id: "3", type: "merge_images", op: "merge_images", params: {} },
        ],
        edges: [
          { from: "1", to: "3", input_port: "image" },
          { from: "2", to: "3", input_port: "mask" },
        ],
      };
      const result = validatePipelineGraph(graph, 3);
      expect(result.valid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });

    it("detects incorrect mask port channel type", () => {
      const graph: PipelineGraph = {
        nodes: [
          { id: "1", type: "basic_input", op: "basic_input", params: {} },
          { id: "2", type: "basic_input", op: "basic_input", params: {} }, // Color image as mask
          { id: "3", type: "merge_images", op: "merge_images", params: {} },
        ],
        edges: [
          { from: "1", to: "3", input_port: "image" },
          { from: "2", to: "3", input_port: "mask" },
        ],
      };
      const result = validatePipelineGraph(graph, 3);
      expect(result.valid).toBe(false);
      
      const maskWarning = result.warnings.find((w) => w.port === "mask");
      expect(maskWarning).toBeDefined();
    });
  });

  describe("recursive branch validation", () => {
    it("validates nested branches in control flow", () => {
      const graph: PipelineGraph = {
        nodes: [
          { id: "1", type: "basic_input", op: "basic_input", params: {} },
          {
            id: "2",
            type: "macro_blend",
            op: "macro_blend",
            params: {},
            branches: {
              left: {
                nodes: [
                  { id: "3", type: "filtering_blur", op: "filtering_blur", params: {} },
                  { id: "4", type: "imageconvertions_grayimage", op: "imageconvertions_grayimage", params: {} },
                  // Color-only operator after grayscale in branch
                  { id: "5", type: "imageconvertions_bgrtohsv", op: "imageconvertions_bgrtohsv", params: {} },
                ],
                edges: [
                  { from: "3", to: "4" },
                  { from: "4", to: "5" },
                ],
              },
              right: { nodes: [], edges: [] },
            },
          },
        ],
        edges: [{ from: "1", to: "2" }],
      };
      const result = validatePipelineGraph(graph, 3);
      expect(result.valid).toBe(false);
      // Should catch the channel mismatch in the nested branch
      expect(result.warnings.length).toBeGreaterThan(0);
    });
  });

  describe("topological sort edge cases", () => {
    it("handles disconnected nodes gracefully", () => {
      const graph: PipelineGraph = {
        nodes: [
          { id: "1", type: "basic_input", op: "basic_input", params: {} },
          { id: "2", type: "filtering_blur", op: "filtering_blur", params: {} },
          // Disconnected node
          { id: "3", type: "imageconvertions_grayimage", op: "imageconvertions_grayimage", params: {} },
        ],
        edges: [{ from: "1", to: "2" }],
      };
      const result = validatePipelineGraph(graph, 3);
      // Should not throw, should process what it can
      expect(result.hasReadImage).toBe(true);
    });
  });
});
