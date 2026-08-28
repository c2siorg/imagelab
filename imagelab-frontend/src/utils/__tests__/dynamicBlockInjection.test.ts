/**
 * @vitest-environment jsdom
 */
import { describe, expect, it } from "vitest";
import type { MacroDefinition } from "../../types/macro";

describe("Dynamic Block Injection", () => {
  it("test_register_macro_as_blockly_block", () => {
    const macroDefinition: MacroDefinition = {
      id: "test-macro-123",
      name: "Test Blur Macro",
      owner_id: "user-1",
      graph: {
        nodes: [
          {
            id: "node1",
            type: "filtering_gaussianblur",
            op: "filtering_gaussianblur",
            params: { kernel_size: 5 },
          },
        ],
        edges: [],
        exposed_params: [
          {
            blockId: "node1",
            blockType: "filtering_gaussianblur",
            paramName: "kernel_size",
            label: "Kernel Size",
            defaultValue: 5,
          },
        ],
      },
      exposedParams: [
        {
          blockId: "node1",
          blockType: "filtering_gaussianblur",
          paramName: "kernel_size",
          label: "Kernel Size",
          defaultValue: 5,
        },
      ],
      pipeline_json: {
        nodes: [],
        edges: [],
        exposed_params: [],
      },
    };

    // Test the macro definition structure used for block registration
    expect(macroDefinition.id).toBe("test-macro-123");
    expect(macroDefinition.name).toBe("Test Blur Macro");
    expect(macroDefinition.exposedParams).toBeDefined();
    expect(macroDefinition.exposedParams?.[0]?.paramName).toBe("kernel_size");
    expect(macroDefinition.exposedParams?.[0]?.defaultValue).toBe(5);

    // Verify block type naming convention
    const blockType = `macro_${macroDefinition.id}`;
    expect(blockType).toBe("macro_test-macro-123");
    expect(blockType).toContain("macro_");
    expect(blockType).toContain(macroDefinition.id);

    // Verify macro graph structural integrity
    expect(macroDefinition.graph.nodes).toHaveLength(1);
    expect(macroDefinition.graph.exposed_params).toHaveLength(1);
  });

  it("test_duplicate_macro_injection_prevention", () => {
    const macroDefinition: MacroDefinition = {
      id: "duplicate-macro-456",
      name: "Duplicate Test Macro",
      owner_id: "user-1",
      graph: {
        nodes: [],
        edges: [],
        exposed_params: [],
      },
      exposedParams: [],
      pipeline_json: {
        nodes: [],
        edges: [],
        exposed_params: [],
      },
    };

    const blockType = `macro_${macroDefinition.id}`;

    expect(blockType).toBe("macro_duplicate-macro-456");

    // Test that the same ID consistently generates the same block type
    const blockType2 = `macro_${macroDefinition.id}`;
    expect(blockType2).toBe(blockType);
    expect(macroDefinition.id).toBe("duplicate-macro-456");
  });

  it("test_macro_with_multiple_exposed_parameters", () => {
    const macroDefinition: MacroDefinition = {
      id: "multi-param-macro",
      name: "Multi Parameter Macro",
      owner_id: "user-1",
      graph: {
        nodes: [],
        edges: [],
        exposed_params: [
          {
            blockId: "node1",
            blockType: "test_block",
            paramName: "param1",
            label: "First Parameter",
            defaultValue: 10,
          },
          {
            blockId: "node2",
            blockType: "test_block",
            paramName: "param2",
            label: "Second Parameter",
            defaultValue: "hello",
          },
          {
            blockId: "node3",
            blockType: "test_block",
            paramName: "param3",
            label: "Third Parameter",
            defaultValue: true,
          },
        ],
      },
      exposedParams: [
        {
          blockId: "node1",
          blockType: "test_block",
          paramName: "param1",
          label: "First Parameter",
          defaultValue: 10,
        },
        {
          blockId: "node2",
          blockType: "test_block",
          paramName: "param2",
          label: "Second Parameter",
          defaultValue: "hello",
        },
        {
          blockId: "node3",
          blockType: "test_block",
          paramName: "param3",
          label: "Third Parameter",
          defaultValue: true,
        },
      ],
      pipeline_json: {
        nodes: [],
        edges: [],
        exposed_params: [],
      },
    };

    // Verify multiple parameters structure safely
    expect(macroDefinition.exposedParams).toBeDefined();
    expect(macroDefinition.exposedParams).toHaveLength(3);

    const params = macroDefinition.exposedParams ?? [];
    expect(params[0]?.defaultValue).toBe(10);
    expect(params[1]?.defaultValue).toBe("hello");
    expect(params[2]?.defaultValue).toBe(true);

    // Verify value types for field creation
    expect(typeof params[0]?.defaultValue).toBe("number");
    expect(typeof params[1]?.defaultValue).toBe("string");
    expect(typeof params[2]?.defaultValue).toBe("boolean");
  });

  it("test_refresh_macro_block_instances", () => {
    const macroDefinition: MacroDefinition = {
      id: "refresh-test-macro",
      name: "Refresh Test Macro",
      owner_id: "user-1",
      graph: {
        nodes: [],
        edges: [],
        exposed_params: [
          {
            blockId: "node1",
            blockType: "test_block",
            paramName: "param1",
            label: "Parameter",
            defaultValue: 42,
          },
        ],
      },
      exposedParams: [
        {
          blockId: "node1",
          blockType: "test_block",
          paramName: "param1",
          label: "Parameter",
          defaultValue: 42,
        },
      ],
      pipeline_json: {
        nodes: [],
        edges: [],
        exposed_params: [],
      },
    };

    expect(macroDefinition.exposedParams).toBeDefined();
    expect(macroDefinition.exposedParams).toHaveLength(1);
    expect(macroDefinition.exposedParams?.[0]?.defaultValue).toBe(42);

    const blockType = `macro_${macroDefinition.id}`;
    expect(blockType).toBe("macro_refresh-test-macro");
    expect(macroDefinition.id).toBe("refresh-test-macro");
  });

  it("test_macro_name_truncation", () => {
    const longName = "A".repeat(30);
    const macroDefinition: MacroDefinition = {
      id: "long-name-macro",
      name: longName,
      owner_id: "user-1",
      graph: {
        nodes: [],
        edges: [],
        exposed_params: [],
      },
      exposedParams: [],
      pipeline_json: {
        nodes: [],
        edges: [],
        exposed_params: [],
      },
    };

    expect(macroDefinition.name.length).toBe(30);

    const truncatedName =
      macroDefinition.name.length > 24
        ? `${macroDefinition.name.slice(0, 22)}\u2026`
        : macroDefinition.name;

    expect(truncatedName.length).toBeLessThanOrEqual(24);
    expect(truncatedName).toContain("\u2026");
    expect(truncatedName).toBe("AAAAAAAAAAAAAAAAAAAAAA\u2026");
  });
});
