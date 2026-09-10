import * as Blockly from "blockly";
import type { ExposedParam, GraphEdge, GraphNode, PipelineGraph } from "../types/macro";
import { cleanFieldLabel, formatExposedFieldKey } from "./macroFieldKeys";
import { useMacroStore } from "../store/useMacroStore";

const INPUT_TYPE_VALUE = 1;
export const EXCLUDED_BLOCK_TYPES = ["basic_readimage", "read_image", "input_image"] as const;
const EXCLUDED_BLOCK_TYPE_SET = new Set<string>(EXCLUDED_BLOCK_TYPES);
const STATIC_FIELD_NAMES = new Set([
  "MACRO_NAME",
  "upload_button",
  "camera_button",
  "filename_label",
]);

// Define helper types to avoid using 'any' while satisfying the linter
type ExtendedField = Blockly.Field & { value?: unknown };
type ExtendedConnection = Blockly.Connection & { getParentInput?: () => Blockly.Input | null };

export function isExcludedMacroBlock(block: Blockly.Block): boolean {
  return EXCLUDED_BLOCK_TYPE_SET.has(block.type);
}

export function filterMacroBlocks(blocks: Blockly.Block[]): Blockly.Block[] {
  return blocks.filter((block) => !isExcludedMacroBlock(block));
}

function isSerializableField(name: string | null): name is string {
  return Boolean(name && !STATIC_FIELD_NAMES.has(name));
}

/** Human-facing nested macro labels must not leak Blockly's internal PB prefix. */
export function cleanNestedMacroParamLabel(name: string): string {
  return cleanFieldLabel(name);
}

function macroIdFromType(type: string): string | null {
  return type.startsWith("macro_") ? type.slice("macro_".length) : null;
}

/**
 * Checks a selected macro subtree against a root macro id. Stored macro graphs
 * supply nested nodes that are not present as live Blockly blocks.
 */
export function hasMacroCycle(macroId: string, selection: Blockly.Block[]): boolean {
  const macros = useMacroStore.getState().macros;
  const byId = new Map(macros.map((macro) => [macro.id, macro]));

  const visitsMacro = (candidateId: string, visiting: Set<string>): boolean => {
    if (candidateId === macroId) return true;
    if (visiting.has(candidateId)) return true;
    const candidate = byId.get(candidateId);
    if (!candidate) return false;
    const nextVisiting = new Set(visiting);
    nextVisiting.add(candidateId);
    return candidate.graph.nodes.some((node) => {
      const nestedId = macroIdFromType(node.type ?? node.op ?? "");
      return nestedId !== null && visitsMacro(nestedId, nextVisiting);
    });
  };

  return selection.some((block) => {
    const selectedMacroId = macroIdFromType(block.type);
    if (selectedMacroId === null) return false;
    if (selectedMacroId !== macroId) return visitsMacro(selectedMacroId, new Set());
    const root = byId.get(macroId);
    return (
      root?.graph.nodes.some((node) => {
        const nestedId = macroIdFromType(node.type ?? node.op ?? "");
        return nestedId !== null && visitsMacro(nestedId, new Set([macroId]));
      }) ?? false
    );
  });
}

/**
 * Traverses sequentially downstream from `startBlock` to `endBlock` using
 * `.getNextBlock()`, capturing each intermediate stack block and any value-input
 * parameter blocks attached to each step.
 *
 * @throws {Error} if `endBlock` is not reachable downstream from `startBlock`.
 */
export function getBlocksBetween(
  startBlock: Blockly.Block,
  endBlock: Blockly.Block,
): Blockly.Block[] {
  if (startBlock.id === endBlock.id) {
    return [startBlock];
  }

  const result: Blockly.Block[] = [];
  const seen = new Set<string>();

  const collectValueInputs = (block: Blockly.Block): void => {
    if (!Array.isArray(block.inputList)) return;
    for (const input of block.inputList) {
      if ((input.type as number) !== INPUT_TYPE_VALUE) continue;
      const attached = input.connection?.targetBlock ? input.connection.targetBlock() : null;
      if (!attached || seen.has(attached.id)) continue;
      seen.add(attached.id);
      result.push(attached);
      // Recursively collect nested value inputs on the attached parameter block
      collectValueInputs(attached);
    }
  };

  let curr: Blockly.Block | null = startBlock;
  while (curr !== null) {
    if (!seen.has(curr.id)) {
      seen.add(curr.id);
      result.push(curr);
      collectValueInputs(curr);
    }

    if (curr.id === endBlock.id) {
      // endBlock reached — collection is complete
      return result;
    }

    curr = typeof curr.getNextBlock === "function" ? curr.getNextBlock() : null;
  }

  throw new Error(
    `Block "${endBlock.type}" (id: ${endBlock.id}) is not downstream of block "${startBlock.type}" (id: ${startBlock.id}). ` +
      "Ensure the end block follows the start block in the same sequential chain.",
  );
}

const INPUT_TYPE_STATEMENT = 3;

const CONTROL_BRANCH_NAME: Record<string, Record<string, string>> = {
  macro_blend: { OP1: "left", OP2: "right" },
  macro_if_else: { IF_BRANCH: "then", ELSE_BRANCH: "else" },
};

/** Serialize a Blockly statement stack to the same graph contract as the root. */
function extractStatementBranch(startBlock: Blockly.Block | null): PipelineGraph {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  let curr = startBlock;
  let previousId: string | null = null;
  while (curr) {
    const childParams: Record<string, unknown> = {};
    const childBranches: Record<string, PipelineGraph> = {};
    if (Array.isArray(curr.inputList)) {
      curr.inputList.forEach((inItem) => {
        if (Array.isArray(inItem.fieldRow)) {
          inItem.fieldRow.forEach((f) => {
            const fname = f.name ?? "";
            if (fname && !STATIC_FIELD_NAMES.has(fname)) {
              childParams[fname] =
                typeof f.getValue === "function" ? f.getValue() : (f as ExtendedField).value;
            }
          });
        }
        if ((inItem.type as number) === INPUT_TYPE_STATEMENT && inItem.connection?.targetBlock) {
          const subTarget = inItem.connection.targetBlock();
          if (subTarget) {
            const subBranch = extractStatementBranch(subTarget);
            // Fallback to an empty string if curr or type is missing
            const branchName = CONTROL_BRANCH_NAME[curr?.type ?? ""]?.[inItem.name ?? ""];
            if (branchName) {
              childBranches[branchName] = subBranch;
            }
          }
        }
      });
    }
    nodes.push({
      id: curr.id,
      type: curr.type,
      op: curr.type,
      params: childParams,
      ...(Object.keys(childBranches).length > 0 ? { branches: childBranches } : {}),
    });
    if (previousId) edges.push({ from: previousId, to: curr.id });
    previousId = curr.id;
    curr = typeof curr.getNextBlock === "function" ? curr.getNextBlock() : null;
  }
  return { nodes, edges };
}

export function extractMacroGraph(
  selectedBlocks: Blockly.Block[],
  allowSingle = false,
  includeExcluded = false,
): PipelineGraph {
  const includedBlocks = includeExcluded ? selectedBlocks : filterMacroBlocks(selectedBlocks);
  if (!includedBlocks || includedBlocks.length < (allowSingle ? 1 : 2)) {
    throw new Error("At least two blocks must be selected to create a macro");
  }

  const selectedIds = new Set<string>();
  const idToBlockMap = new Map<string, Blockly.Block>();

  for (const block of includedBlocks) {
    if (!block || !block.id) {
      throw new Error("Invalid block in selection");
    }
    if (selectedIds.has(block.id)) {
      throw new Error(`Duplicate block ID found in selection: ${block.id}`);
    }
    selectedIds.add(block.id);
    idToBlockMap.set(block.id, block);
  }

  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  const edgeSet = new Set<string>();

  const addEdge = (from: string, to: string, inputPort?: string | null) => {
    if (from === to) return;
    const key = `${from}->${to}:${inputPort || ""}`;
    if (!edgeSet.has(key)) {
      edgeSet.add(key);
      edges.push({
        from,
        to,
        ...(inputPort ? { input_port: inputPort } : {}),
      });
    }
  };

  // 1. Build Nodes and extract edges from all possible connection types
  for (const block of includedBlocks) {
    const params: Record<string, unknown> = {};
    const branches: Record<string, PipelineGraph> = {};

    if (Array.isArray(block.inputList)) {
      block.inputList.forEach((input) => {
        // Extract fields
        if (Array.isArray(input.fieldRow)) {
          input.fieldRow.forEach((field) => {
            const fieldName = field.name ?? "";
            if (
              isSerializableField(fieldName) ||
              (includeExcluded && isExcludedMacroBlock(block))
            ) {
              params[fieldName] =
                typeof field.getValue === "function"
                  ? field.getValue()
                  : (field as ExtendedField).value;
            }
          });
        }

        // Check input connection (upstream provider)
        const connected = input.connection?.targetBlock ? input.connection.targetBlock() : null;
        if (connected) {
          if (selectedIds.has(connected.id)) {
            // Directed edge from connected block to current block on this input port
            addEdge(connected.id, block.id, input.name || null);
          } else if ((input.type as number) === INPUT_TYPE_STATEMENT) {
            const statementBranch = extractStatementBranch(connected);
            const branchName = CONTROL_BRANCH_NAME[block.type]?.[input.name ?? ""];
            if (branchName) branches[branchName] = statementBranch;
          } else if (
            (input.type as number) === INPUT_TYPE_VALUE &&
            Array.isArray(connected.inputList)
          ) {
            // Unselected value block attached as parameter provider
            connected.inputList.forEach((childInput) => {
              if (Array.isArray(childInput.fieldRow)) {
                childInput.fieldRow.forEach((field) => {
                  const fieldName = field.name ?? "";
                  if (isSerializableField(fieldName)) {
                    params[fieldName] =
                      typeof field.getValue === "function"
                        ? field.getValue()
                        : (field as ExtendedField).value;
                  }
                });
              }
            });
          }
        }
      });
    }

    // Check next connection (downstream block in sequence)
    const nextBlock =
      typeof block.getNextBlock === "function"
        ? block.getNextBlock()
        : block.nextConnection?.targetBlock
          ? block.nextConnection.targetBlock()
          : null;

    if (nextBlock && selectedIds.has(nextBlock.id)) {
      addEdge(block.id, nextBlock.id);
    }

    // Check previous connection (upstream block in sequence) - handles sink blocks & mid-chain
    const prevBlock = block.previousConnection?.targetBlock
      ? block.previousConnection.targetBlock()
      : null;

    if (prevBlock && selectedIds.has(prevBlock.id)) {
      addEdge(prevBlock.id, block.id);
    }

    // Check value output connection (for source/value blocks connected via output)
    const outputTargetConn = block.outputConnection?.targetConnection;
    if (outputTargetConn && typeof outputTargetConn.getSourceBlock === "function") {
      const outputTargetBlock = outputTargetConn.getSourceBlock();
      if (outputTargetBlock && selectedIds.has(outputTargetBlock.id)) {
        const extConn = outputTargetConn as ExtendedConnection;
        const inputPort =
          typeof extConn.getParentInput === "function"
            ? extConn.getParentInput()?.name || null
            : null;
        addEdge(block.id, outputTargetBlock.id, inputPort);
      }
    }

    nodes.push({
      id: block.id,
      type: block.type,
      op: block.type,
      params,
      ...(Object.keys(branches).length > 0 ? { branches } : {}),
    });
  }

  // 2. Validate Connected Component — undirected BFS so source blocks (no
  //    previousConnection) and sink blocks (no nextConnection) are valid roots/leaves.
  //    Only throw if the graph is genuinely disconnected (isolated floating blocks).
  const adj = new Map<string, Set<string>>();
  selectedIds.forEach((id) => adj.set(id, new Set()));

  for (const edge of edges) {
    // Build undirected adjacency so a source at position 0 can still reach all nodes
    adj.get(edge.from)?.add(edge.to);
    adj.get(edge.to)?.add(edge.from);
  }

  // Start BFS from the node with the most outgoing edges — avoids false failures
  // when selectedBlocks[0] happens to be a pure sink with no edges yet discovered.
  let bfsStartId = includedBlocks[0].id;
  let maxDegree = adj.get(bfsStartId)?.size ?? 0;
  for (const [id, neighbors] of adj) {
    if (neighbors.size > maxDegree) {
      maxDegree = neighbors.size;
      bfsStartId = id;
    }
  }

  const visited = new Set<string>();
  const queue: string[] = [bfsStartId];
  visited.add(bfsStartId);

  while (queue.length > 0) {
    const curr = queue.shift()!;
    const neighbors = adj.get(curr);
    if (neighbors) {
      for (const nbr of neighbors) {
        if (!visited.has(nbr)) {
          visited.add(nbr);
          queue.push(nbr);
        }
      }
    }
  }

  if (visited.size !== selectedIds.size) {
    throw new Error(
      "Selection contains floating/unconnected blocks. " +
        "Ensure all selected blocks form a single connected chain.",
    );
  }

  return { nodes, edges };
}

/** The one workspace-to-graph serializer used for execution and persistence. */
export function extractWorkspaceGraph(workspace: Blockly.WorkspaceSvg): PipelineGraph {
  const root = workspace
    .getTopBlocks(true)
    .find((block) => EXCLUDED_BLOCK_TYPE_SET.has(block.type));
  if (!root) return { nodes: [], edges: [] };
  const blocks: Blockly.Block[] = [];
  let current: Blockly.Block | null = root;
  while (current) {
    blocks.push(current);
    current = typeof current.getNextBlock === "function" ? current.getNextBlock() : null;
  }
  return extractMacroGraph(blocks, true, true);
}
export function getCleanBlockDisplayName(block: Blockly.Block): string {
  // 1. Check if the block has a human-readable title field on the canvas
  const displayTitle =
    (typeof block.getFieldValue === "function"
      ? block.getFieldValue("TITLE") || block.getFieldValue("MACRO_TITLE")
      : null) ?? (block as unknown as { macroName?: string }).macroName;

  // Only use displayTitle if it's NOT a raw macro ID (starts with macro_) or serialized key
  if (
    displayTitle &&
    typeof displayTitle === "string" &&
    displayTitle.trim() &&
    !displayTitle.startsWith("macro_") &&
    !displayTitle.includes("|")
  ) {
    return cleanFieldLabel(displayTitle);
  }

  // 2. Check if it is a TRUE user-defined macro block
  if (block.type && block.type.startsWith("macro_")) {
    const rawId = block.type.replace(/^macro_/, "");
    const realMacro = useMacroStore.getState().macros.find((m) => m.id === rawId);
    if (realMacro && realMacro.name) {
      return realMacro.name;
    }
  }

  // 3. Standard / Built-in Pipeline Blocks
  let cleanType = (block.type || "").replace(
    /^(macro_|geometric_|filtering_|morphological_|color_|edge_|transform_|annotation_|drawing_|basic_|op_)/,
    "",
  );

  cleanType = cleanType
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/drawline/i, "draw line")
    .replace(/drawcircle/i, "draw circle")
    .replace(/drawrectangle/i, "draw rectangle")
    .replace(/drawtext/i, "draw text")
    .replace(/cropimage/i, "crop image")
    .replace(/contourdetection/i, "contour detection")
    .replace(/_+/g, " ");

  return cleanType
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

/**
 * Determines if a block is a macro block (starts with macro_ or macro-)
 */
function isMacroBlockType(blockType: string): boolean {
  return blockType.startsWith("macro_") || blockType.startsWith("macro-");
}
export function extractExposedParamCandidates(selectedBlocks: Blockly.Block[]): ExposedParam[] {
  const params: ExposedParam[] = [];
  const seenKeys = new Set<string>();

  for (const block of filterMacroBlocks(selectedBlocks)) {
    if (!block || !Array.isArray(block.inputList)) continue;

    const displayBlockType = getCleanBlockDisplayName(block);

    block.inputList.forEach((input) => {
      if (Array.isArray(input.fieldRow)) {
        input.fieldRow.forEach((field) => {
          const fieldName = field.name ?? "";
          if (isSerializableField(fieldName)) {
            const key = formatExposedFieldKey(block.id, fieldName);
            if (!seenKeys.has(key)) {
              seenKeys.add(key);
              const val =
                typeof field.getValue === "function"
                  ? field.getValue()
                  : (field as ExtendedField).value;

              const cleanParamName = cleanFieldLabel(fieldName);

              // For nested macro blocks, preserve lowercase parent macro name in suffix
              let labelSuffix = displayBlockType;
              if (block.type && isMacroBlockType(block.type)) {
                // For nested macros, use the raw block type in lowercase (e.g., "macro-child")
                labelSuffix = block.type.toLowerCase();
              }

              params.push({
                blockId: block.id,
                blockType: block.type,
                paramName: fieldName,
                label: `${cleanParamName} (${labelSuffix})`,
                defaultValue: val,
              });
            }
          }
        });
      }
    });
  }

  return params;
}
export function getSelectedBlocksFromBlock(startBlock: Blockly.Block): Blockly.Block[] {
  if (!startBlock) return [];
  const collectedSet = new Set<string>();
  const result: Blockly.Block[] = [];

  let curr: Blockly.Block | null = startBlock;
  while (curr) {
    if (!collectedSet.has(curr.id)) {
      collectedSet.add(curr.id);
      result.push(curr);
    }

    if (Array.isArray(curr.inputList)) {
      curr.inputList.forEach((input) => {
        const target = input.connection?.targetBlock ? input.connection.targetBlock() : null;
        if (target && !collectedSet.has(target.id)) {
          collectedSet.add(target.id);
          result.push(target);
        }
      });
    }

    curr = typeof curr.getNextBlock === "function" ? curr.getNextBlock() : null;
  }

  return result;
}

export function getSelectedBlocks(workspace: Blockly.WorkspaceSvg | null): Blockly.Block[] {
  if (!workspace || typeof document === "undefined") return [];

  const selected = Blockly.common ? Blockly.common.getSelected() : null;
  if (!selected) return [];

  let initialBlocks: Blockly.Block[] = [];

  if (Array.isArray(selected)) {
    initialBlocks = selected.filter((b): b is Blockly.Block =>
      Boolean(b && typeof b === "object" && "id" in b && "type" in b),
    );
  } else if (typeof selected === "object" && "id" in selected && "type" in selected) {
    initialBlocks = [selected as unknown as Blockly.Block];
  }

  if (initialBlocks.length === 0) return [];

  const collectedSet = new Set<string>();
  const result: Blockly.Block[] = [];

  for (const blk of initialBlocks) {
    const chain = getSelectedBlocksFromBlock(blk);
    for (const item of chain) {
      if (!collectedSet.has(item.id)) {
        collectedSet.add(item.id);
        result.push(item);
      }
    }
  }

  return result;
}
