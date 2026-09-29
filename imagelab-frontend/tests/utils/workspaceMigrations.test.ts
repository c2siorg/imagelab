/**
 * @vitest-environment jsdom
 */
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import * as Blockly from "blockly";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { extractPipeline } from "../../src/hooks/usePipeline";
import type { WorkspaceJson } from "../../src/types/blocklyWorkspace";
import { loadWorkspaceState } from "../../src/utils/workspaceLoad";
import { migrateWorkspaceJson } from "../../src/utils/workspaceMigrations";

const workspaces: Blockly.Workspace[] = [];

function headlessWorkspace(): Blockly.WorkspaceSvg {
  const ws = new Blockly.Workspace();
  workspaces.push(ws);
  // loadWorkspaceState and extractPipeline only use Workspace methods.
  return ws as unknown as Blockly.WorkspaceSvg;
}

/** Workspace saved by the old two-field affine block: Read Image -> Affine (translate 20, 5). */
function legacyAffineWorkspace(affineFields: Record<string, unknown>): WorkspaceJson {
  return {
    blocks: {
      languageVersion: 0,
      blocks: [
        {
          type: "basic_readimage",
          id: "read-1",
          x: 20,
          y: 20,
          next: {
            block: { type: "geometric_affineimage", id: "affine-1", fields: affineFields },
          },
        },
      ],
    },
  };
}

const LEGACY_FIELDS = { translate_x: 20, translate_y: 5 };
const EXPECTED_SRC = { src_x1: 0, src_y1: 0, src_x2: 100, src_y2: 0, src_x3: 0, src_y3: 100 };
const EXPECTED_DST = { dst_x1: 20, dst_y1: 5, dst_x2: 120, dst_y2: 5, dst_x3: 20, dst_y3: 105 };

beforeAll(() => {
  setupBlocklyFields();
  registerAllBlocks();
});

afterEach(() => {
  workspaces.splice(0).forEach((ws) => ws.dispose());
});

describe("migrateWorkspaceJson", () => {
  it("rewrites legacy translate_x / translate_y into shifted destination points", () => {
    const migrated = migrateWorkspaceJson(legacyAffineWorkspace(LEGACY_FIELDS));
    const affine = migrated.blocks.blocks[0].next.block;
    expect(affine.fields).toEqual({ ...EXPECTED_SRC, ...EXPECTED_DST });
  });

  it("does not mutate the input and leaves current-format blocks alone", () => {
    const current = legacyAffineWorkspace({ ...EXPECTED_SRC, dst_x1: 7, dst_y1: 7 });
    const snapshot = structuredClone(current);
    const migrated = migrateWorkspaceJson(current);
    expect(current).toEqual(snapshot);
    expect(migrated).toEqual(snapshot);
  });

  it("migrates affine blocks nested inside statement inputs", () => {
    const state: WorkspaceJson = {
      blocks: {
        languageVersion: 0,
        blocks: [
          {
            type: "macro_blend",
            id: "blend-1",
            inputs: {
              BRANCH_A: { block: { type: "geometric_affineimage", fields: LEGACY_FIELDS } },
            },
          },
        ],
      },
    };
    const migrated = migrateWorkspaceJson(state);
    expect(migrated.blocks.blocks[0].inputs.BRANCH_A.block.fields).toEqual({
      ...EXPECTED_SRC,
      ...EXPECTED_DST,
    });
  });
});

describe("loading a workspace saved by the old affine block", () => {
  it("restores the translation as destination points and sends it to the backend", () => {
    const workspace = headlessWorkspace();
    loadWorkspaceState(workspace, legacyAffineWorkspace(LEGACY_FIELDS));

    const affine = workspace.getBlockById("affine-1");
    expect(affine).not.toBeNull();
    for (const [name, value] of Object.entries({ ...EXPECTED_SRC, ...EXPECTED_DST })) {
      expect(affine!.getFieldValue(name)).toBe(value);
    }

    const pipeline = extractPipeline(workspace);
    const step = pipeline.find((s) => s.type === "geometric_affineimage");
    expect(step?.params).toEqual({ ...EXPECTED_SRC, ...EXPECTED_DST });
    expect(step?.params).not.toHaveProperty("translate_x");
  });
});
