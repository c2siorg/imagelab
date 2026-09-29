import { geometricBlocks } from "../blocks/definitions/geometric.blocks";
import type { WorkspaceJson } from "../types/blocklyWorkspace";

const AFFINE_BLOCK_TYPE = "geometric_affineimage";
const AFFINE_POINT_SUFFIXES = ["x1", "y1", "x2", "y2", "x3", "y3"] as const;

type BlockJson = {
  type?: string;
  fields?: Record<string, unknown>;
  next?: { block?: BlockJson; shadow?: BlockJson };
  inputs?: Record<string, { block?: BlockJson; shadow?: BlockJson }>;
};

/**
 * Upgrades workspace JSON saved by older block definitions so it loads with the
 * current ones. Blockly silently drops fields a block no longer declares, so
 * without this an old block would come back with default values.
 *
 * Runs on every load path (autosave restore, saved pipelines, version history,
 * shared links, file import). Returns a new object; the input is not mutated.
 */
export function migrateWorkspaceJson<T extends WorkspaceJson>(state: T): T {
  const migrated = structuredClone(state);
  const blocks = migrated?.blocks?.blocks;
  if (Array.isArray(blocks)) {
    blocks.forEach(migrateBlockTree);
  }
  return migrated;
}

function migrateBlockTree(block: BlockJson | undefined): void {
  if (!block) return;
  if (block.type === AFFINE_BLOCK_TYPE) {
    migrateLegacyAffineFields(block);
  }
  migrateBlockTree(block.next?.block);
  migrateBlockTree(block.next?.shadow);
  Object.values(block.inputs ?? {}).forEach((input) => {
    migrateBlockTree(input.block);
    migrateBlockTree(input.shadow);
  });
}

/**
 * The affine block used to expose only translate_x / translate_y. Express that
 * translation as the current three-point form: keep the default source points
 * and shift every destination point by (translate_x, translate_y).
 */
function migrateLegacyAffineFields(block: BlockJson): void {
  const fields = block.fields ?? {};
  const isLegacy = "translate_x" in fields || "translate_y" in fields;
  const hasPoints = Object.keys(fields).some((name) => name.startsWith("dst_"));
  if (!isLegacy || hasPoints) return;

  const tx = Number(fields.translate_x ?? 0) || 0;
  const ty = Number(fields.translate_y ?? 0) || 0;
  const migrated: Record<string, unknown> = {};
  for (const suffix of AFFINE_POINT_SUFFIXES) {
    const src = Number(fields[`src_${suffix}`] ?? affineFieldDefault(`src_${suffix}`));
    migrated[`src_${suffix}`] = src;
    migrated[`dst_${suffix}`] = src + (suffix.startsWith("x") ? tx : ty);
  }
  block.fields = migrated;
}

function affineFieldDefault(name: string): number {
  const definition = geometricBlocks.find((def) => def.type === AFFINE_BLOCK_TYPE);
  const arg = definition?.args0.find((a) => "name" in a && a.name === name);
  return arg && "value" in arg && typeof arg.value === "number" ? arg.value : 0;
}
