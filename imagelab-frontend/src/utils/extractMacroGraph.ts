import * as Blockly from "blockly";
import type { ExposedParam, GraphEdge, GraphNode, PipelineGraph } from "../types/macro";

const INPUT_TYPE_VALUE = 1;

// Define helper types to avoid using 'any' while satisfying the linter
type ExtendedField = Blockly.Field & { value?: unknown };
type ExtendedConnection = Blockly.Connection & { getParentInput?: () => Blockly.Input | null };

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

export function extractMacroGraph(selectedBlocks: Blockly.Block[]): PipelineGraph {
  if (!selectedBlocks || selectedBlocks.length < 2) {
    throw new Error("At least two blocks must be selected to create a macro");
  }

  const selectedIds = new Set<string>();
  const idToBlockMap = new Map<string, Blockly.Block>();

  for (const block of selectedBlocks) {
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
  for (const block of selectedBlocks) {
    const params: Record<string, unknown> = {};

    if (Array.isArray(block.inputList)) {
      block.inputList.forEach((input) => {
        // Extract fields
        if (Array.isArray(input.fieldRow)) {
          input.fieldRow.forEach((field) => {
            if (field.name) {
              params[field.name] =
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
          } else if (
            (input.type as number) === INPUT_TYPE_VALUE &&
            Array.isArray(connected.inputList)
          ) {
            // Unselected value block attached as parameter provider
            connected.inputList.forEach((childInput) => {
              if (Array.isArray(childInput.fieldRow)) {
                childInput.fieldRow.forEach((field) => {
                  if (field.name) {
                    params[field.name] =
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
  let bfsStartId = selectedBlocks[0].id;
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

export function extractExposedParamCandidates(selectedBlocks: Blockly.Block[]): ExposedParam[] {
  const params: ExposedParam[] = [];
  const seenKeys = new Set<string>();

  for (const block of selectedBlocks) {
    if (!block || !Array.isArray(block.inputList)) continue;
    block.inputList.forEach((input) => {
      if (Array.isArray(input.fieldRow)) {
        input.fieldRow.forEach((field) => {
          if (field.name) {
            const key = `${block.id}:${field.name}`;
            if (!seenKeys.has(key)) {
              seenKeys.add(key);
              const val =
                typeof field.getValue === "function"
                  ? field.getValue()
                  : (field as ExtendedField).value;
              params.push({
                blockId: block.id,
                blockType: block.type,
                paramName: field.name,
                label: `${field.name} (${block.type})`,
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
