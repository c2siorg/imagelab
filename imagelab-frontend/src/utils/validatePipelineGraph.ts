import type { PipelineGraph, GraphNode } from "../types/macro";

export interface ValidationWarning {
  nodeId: string;
  nodeType: string;
  message: string;
  port?: string;
}

export interface ValidationResult {
  valid: boolean;
  warnings: ValidationWarning[];
  hasReadImage: boolean;
}

// Port specifications matching backend OPERATOR_PORT_SPECS
const OPERATOR_PORT_SPECS: Record<string, Record<string, number[]>> = {
  imageconvertions_grayimage: { image: [3, 4], input: [3, 4] },
  imageconvertions_colortobinary: { image: [3, 4], input: [3, 4] },
  imageconvertions_graytobinary: { image: [1], input: [1] },
  imageconvertions_channelsplit: { image: [3, 4], input: [3, 4] },
  imageconvertions_hsvtobgr: { image: [3], input: [3] },
  imageconvertions_bgrtohsv: { image: [3, 4], input: [3, 4] },
  imageconvertions_bgrtolab: { image: [3, 4], input: [3, 4] },
  imageconvertions_labtobgr: { image: [3], input: [3] },
  imageconvertions_bgrtoycrcb: { image: [3, 4], input: [3, 4] },
  imageconvertions_ycrcbtobgr: { image: [3], input: [3] },
  thresholding_adaptivethreshold: { image: [1], input: [1] },
  thresholding_otsuthreshold: { image: [1], input: [1] },
  merge_images: { image: [3, 4], mask: [1] },
  blend_images: { image: [3, 4], mask: [1] },
};

// Output channel specifications matching backend OPERATOR_OUTPUT_CHANNELS
const OPERATOR_OUTPUT_CHANNELS: Record<string, number> = {
  imageconvertions_grayimage: 1,
  imageconvertions_colortobinary: 1,
  imageconvertions_graytobinary: 1,
  imageconvertions_channelsplit: 1,
  thresholding_applythreshold: 1,
  thresholding_adaptivethreshold: 1,
  thresholding_otsuthreshold: 1,
  filtering_cannyedge: 3,
  segmentation_watershed: 3,
  transformation_distance: 1,
};

// Control flow operators with branch requirements
const CONTROL_BRANCHES: Record<string, string[]> = {
  macro_blend: ["left", "right"],
  macro_if_else: ["then", "else"],
};

function getNodeType(node: GraphNode): string {
  return node.type || node.op || "";
}

function topologicalSort(graph: PipelineGraph): string[] {
  const inDegree: Record<string, number> = {};
  const adj: Record<string, string[]> = {};

  // Initialize
  for (const node of graph.nodes) {
    inDegree[node.id] = 0;
    adj[node.id] = [];
  }

  // Build adjacency list and calculate in-degrees
  for (const edge of graph.edges) {
    adj[edge.from].push(edge.to);
    inDegree[edge.to] = (inDegree[edge.to] || 0) + 1;
  }

  // Collect nodes with no incoming edges
  const queue: string[] = [];
  for (const node of graph.nodes) {
    if (inDegree[node.id] === 0) {
      queue.push(node.id);
    }
  }

  // Sort deterministically
  queue.sort();

  const result: string[] = [];
  while (queue.length > 0) {
    const nodeId = queue.shift()!;
    result.push(nodeId);

    const neighbors = adj[nodeId] || [];
    const nextReady: string[] = [];

    for (const neighbor of neighbors) {
      inDegree[neighbor]--;
      if (inDegree[neighbor] === 0) {
        nextReady.push(neighbor);
      }
    }

    // Add to queue in sorted order
    nextReady.sort();
    queue.push(...nextReady);
  }

  return result;
}

function getHumanReadableOperatorName(nodeType: string): string {
  // Remove common prefixes
  let cleanType = nodeType.replace(
    /^(imageconvertions_|thresholding_|filtering_|morphological_|geometric_|segmentation_|transformation_|annotation_|drawing_)/,
    "",
  );

  // Convert to title case with spaces
  cleanType = cleanType
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");

  return cleanType;
}

function getChannelTypeName(channels: number): string {
  if (channels === 1) return "grayscale (1 channel)";
  if (channels === 3) return "color (3 channels)";
  if (channels === 4) return "color with alpha (4 channels)";
  return `${channels} channels`;
}

/**
 * Validates a pipeline graph for type mismatches and structural issues.
 * Mirrors the backend _validate_graph logic in graph_engine.py.
 *
 * @param graph - The pipeline graph to validate
 * @param inputChannels - Expected input channels (default: 3 for color)
 * @param isNestedBranch - Whether this is a nested branch (skips Read Image check)
 */
export function validatePipelineGraph(
  graph: PipelineGraph,
  inputChannels: number = 3,
  isNestedBranch: boolean = false,
): ValidationResult {
  const warnings: ValidationWarning[] = [];

  // Check for Read Image block (only in root graph, not in branches)
  const hasReadImage = graph.nodes.some((node) => {
    const nodeType = getNodeType(node);
    return nodeType === "basic_input" || nodeType === "readimage" || nodeType === "read_image";
  });

  if (!isNestedBranch && !hasReadImage && graph.nodes.length > 0) {
    warnings.push({
      nodeId: "",
      nodeType: "",
      message:
        'No "Read Image" block found. Add a "Read Image" block to load an image into the pipeline.',
    });
  }

  // Track output channels for each node
  const outputs: Record<string, number> = {};
  const nodes = new Map(graph.nodes.map((n) => [n.id, n]));

  try {
    const sortedNodes = topologicalSort(graph);

    for (const nodeId of sortedNodes) {
      const node = nodes.get(nodeId);
      if (!node) continue;

      const nodeType = getNodeType(node);

      // Get incoming edges
      const incoming = graph.edges.filter((edge) => edge.to === nodeId);

      // Build port mapping
      const ports: Record<string, number> = {};
      for (const edge of incoming) {
        const sourceChannels = outputs[edge.from];
        if (sourceChannels !== undefined) {
          const port = edge.input_port || "image";
          ports[port] = sourceChannels;
        }
      }

      // Determine primary input channels
      let primary = inputChannels;
      if (incoming.length > 0) {
        // Try to find the primary port (None, image, or input)
        primary = ports.image || ports.input || Object.values(ports)[0] || inputChannels;
      }

      // Validate port channels against specs
      const portSpecs = OPERATOR_PORT_SPECS[nodeType];
      if (portSpecs) {
        for (const [port, channels] of Object.entries(ports)) {
          const allowed = portSpecs[port] || portSpecs.image || portSpecs.input;
          if (allowed && !allowed.includes(channels)) {
            const humanName = getHumanReadableOperatorName(nodeType);
            const expectedStr = allowed.map(getChannelTypeName).join(" or ");
            const gotStr = getChannelTypeName(channels);

            warnings.push({
              nodeId,
              nodeType,
              port,
              message: `"${humanName}" block expects ${expectedStr} but received ${gotStr}. Check the blocks connected before this one.`,
            });
          }
        }
      }

      // Validate control flow branches
      if (CONTROL_BRANCHES[nodeType]) {
        const required = CONTROL_BRANCHES[nodeType];
        const branchNames = Object.keys(node.branches || {});
        const missingBranches = required.filter((name) => !branchNames.includes(name));

        if (missingBranches.length > 0) {
          const humanName = getHumanReadableOperatorName(nodeType);
          warnings.push({
            nodeId,
            nodeType,
            message: `"${humanName}" control block requires ${required.join(" and ")} branches, but ${missingBranches.join(", ")} ${missingBranches.length === 1 ? "is" : "are"} missing.`,
          });
        }

        // Recursively validate branches
        if (node.branches) {
          for (const branchGraph of Object.values(node.branches)) {
            if (typeof branchGraph === "object" && "nodes" in branchGraph) {
              const branchResult = validatePipelineGraph(
                branchGraph as PipelineGraph,
                primary,
                true,
              );
              warnings.push(...branchResult.warnings);
            }
          }
        }
      }

      // Calculate output channels for this node
      outputs[nodeId] = OPERATOR_OUTPUT_CHANNELS[nodeType] ?? primary;
    }
  } catch (error) {
    // If topological sort fails (cycle), that's handled by backend
    // We focus on type checking here
    console.warn("Topological sort failed, skipping validation:", error);
  }

  return {
    valid: warnings.length === 0,
    warnings,
    hasReadImage,
  };
}
