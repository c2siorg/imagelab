/**
 * @vitest-environment jsdom
 */
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import * as Blockly from "blockly";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { registerAllBlocks } from "../../src/blocks/definitions";
import { loadWorkspaceState } from "../../src/utils/workspaceLoad";
import {
  DEFAULT_PIPELINE_FILE_NAME,
  PIPELINE_FILE_SCHEMA_VERSION,
  PipelineFileError,
  buildPipelineFile,
  parsePipelineFile,
  pipelineFileName,
  readFileText,
  serializePipelineFile,
} from "../../src/utils/pipelineFile";

const workspaces: Blockly.Workspace[] = [];

function headlessWorkspace(): Blockly.WorkspaceSvg {
  const ws = new Blockly.Workspace();
  workspaces.push(ws);
  // loadWorkspaceState only uses Workspace methods, so a headless workspace is enough here.
  return ws as unknown as Blockly.WorkspaceSvg;
}

/** Two connected blocks with non-default field values plus a detached block at its own position. */
function buildSamplePipeline(workspace: Blockly.Workspace): void {
  const blur = workspace.newBlock("blurring_applygaussianblur", "blur-1");
  blur.setFieldValue(7, "widthSize");
  blur.setFieldValue(5, "heightSize");
  blur.moveBy(40, 60);

  const scale = workspace.newBlock("geometric_scaleimage", "scale-1");
  scale.setFieldValue(0.5, "fx");
  scale.setFieldValue(1.25, "fy");
  scale.setFieldValue("CUBIC", "interpolation");
  blur.nextConnection!.connect(scale.previousConnection!);

  const reflect = workspace.newBlock("geometric_reflectimage", "reflect-1");
  reflect.setFieldValue("Both", "type");
  reflect.moveBy(300, 120);
}

beforeAll(() => {
  setupBlocklyFields();
  registerAllBlocks();
});

afterEach(() => {
  workspaces.splice(0).forEach((ws) => ws.dispose());
});

describe("buildPipelineFile", () => {
  it("carries the schema version, the pipeline name and the Blockly save output", () => {
    const ws = headlessWorkspace();
    buildSamplePipeline(ws);

    const file = buildPipelineFile(ws, "My Blur");

    expect(file.schemaVersion).toBe(PIPELINE_FILE_SCHEMA_VERSION);
    expect(file.name).toBe("My Blur");
    expect(file.workspace).toEqual(Blockly.serialization.workspaces.save(ws));
    expect(file.workspace.blocks.blocks.map((b: { id: string }) => b.id)).toEqual([
      "blur-1",
      "reflect-1",
    ]);
  });

  it("falls back to a default name when no pipeline is open", () => {
    const ws = headlessWorkspace();

    expect(buildPipelineFile(ws, null).name).toBe(DEFAULT_PIPELINE_FILE_NAME);
    expect(buildPipelineFile(ws, "   ").name).toBe(DEFAULT_PIPELINE_FILE_NAME);
  });
});

describe("serializePipelineFile", () => {
  it("writes JSON that parses back to the same payload", () => {
    const ws = headlessWorkspace();
    buildSamplePipeline(ws);
    const file = buildPipelineFile(ws, "Sample");

    const text = serializePipelineFile(file);

    expect(JSON.parse(text)).toEqual(file);
    expect(text.startsWith("{\n")).toBe(true);
  });
});

describe("pipelineFileName", () => {
  it("slugs the pipeline name and appends .json", () => {
    expect(pipelineFileName("My Blur Pipeline")).toBe("my-blur-pipeline.json");
    expect(pipelineFileName("  Edge / Detect (v2)! ")).toBe("edge-detect-v2.json");
    expect(pipelineFileName("")).toBe(`${DEFAULT_PIPELINE_FILE_NAME}.json`);
    expect(pipelineFileName("???")).toBe(`${DEFAULT_PIPELINE_FILE_NAME}.json`);
  });
});

describe("export then import", () => {
  it("round-trips field values, block positions and connections", () => {
    const source = headlessWorkspace();
    buildSamplePipeline(source);
    const exported = buildPipelineFile(source, "Sample");

    const target = headlessWorkspace();
    const imported = parsePipelineFile(serializePipelineFile(exported));
    loadWorkspaceState(target, imported.workspace);

    expect(imported.name).toBe("Sample");
    expect(Blockly.serialization.workspaces.save(target)).toEqual(exported.workspace);

    const blur = target.getBlockById("blur-1")!;
    expect(blur.getFieldValue("widthSize")).toBe(7);
    expect(blur.getFieldValue("heightSize")).toBe(5);
    expect(blur.getRelativeToSurfaceXY()).toEqual(new Blockly.utils.Coordinate(40, 60));
    expect(blur.getNextBlock()?.id).toBe("scale-1");

    const scale = target.getBlockById("scale-1")!;
    expect(scale.getFieldValue("fx")).toBe(0.5);
    expect(scale.getFieldValue("fy")).toBe(1.25);
    expect(scale.getFieldValue("interpolation")).toBe("CUBIC");

    const reflect = target.getBlockById("reflect-1")!;
    expect(reflect.getFieldValue("type")).toBe("Both");
    expect(reflect.getRelativeToSurfaceXY()).toEqual(new Blockly.utils.Coordinate(300, 120));
  });

  it("accepts an export of an empty workspace", () => {
    const source = headlessWorkspace();
    const target = headlessWorkspace();
    buildSamplePipeline(target);

    const imported = parsePipelineFile(serializePipelineFile(buildPipelineFile(source, null)));
    loadWorkspaceState(target, imported.workspace);

    expect(target.getAllBlocks(false)).toHaveLength(0);
  });

  it("restores the previous blocks when the file references an unknown block type", () => {
    const target = headlessWorkspace();
    buildSamplePipeline(target);
    const before = Blockly.serialization.workspaces.save(target);

    const imported = parsePipelineFile(
      JSON.stringify({
        schemaVersion: PIPELINE_FILE_SCHEMA_VERSION,
        name: "Broken",
        workspace: {
          blocks: { languageVersion: 0, blocks: [{ type: "not_a_real_block", id: "x" }] },
        },
      }),
    );

    expect(() => loadWorkspaceState(target, imported.workspace)).toThrow();
    expect(Blockly.serialization.workspaces.save(target)).toEqual(before);
  });
});

describe("parsePipelineFile", () => {
  const valid = {
    schemaVersion: PIPELINE_FILE_SCHEMA_VERSION,
    name: "Sample",
    workspace: { blocks: { languageVersion: 0, blocks: [] } },
  };

  it("rejects text that is not JSON", () => {
    expect(() => parsePipelineFile("{ not json")).toThrow(PipelineFileError);
    expect(() => parsePipelineFile("{ not json")).toThrow("not valid JSON");
  });

  it("rejects JSON that is not a pipeline export", () => {
    for (const text of ["[]", "null", '"text"', "{}", '{"name":"x"}', '{"workspace":{}}']) {
      expect(() => parsePipelineFile(text)).toThrow("not an ImageLab pipeline export");
    }
  });

  it("rejects a schema version this build does not read", () => {
    const text = JSON.stringify({ ...valid, schemaVersion: PIPELINE_FILE_SCHEMA_VERSION + 1 });

    expect(() => parsePipelineFile(text)).toThrow(
      `Unsupported pipeline file version ${PIPELINE_FILE_SCHEMA_VERSION + 1}`,
    );
    expect(() => parsePipelineFile(JSON.stringify({ ...valid, schemaVersion: "1" }))).toThrow(
      "Unsupported pipeline file version",
    );
  });

  it("rejects workspace data that Blockly cannot load", () => {
    const badWorkspaces = [null, "blocks", [], { blocks: [] }, { blocks: { blocks: {} } }];
    for (const workspace of badWorkspaces) {
      expect(() => parsePipelineFile(JSON.stringify({ ...valid, workspace }))).toThrow(
        "does not contain valid workspace data",
      );
    }
  });

  it("returns the payload and defaults a missing name", () => {
    expect(parsePipelineFile(JSON.stringify(valid))).toEqual(valid);
    expect(parsePipelineFile(JSON.stringify({ ...valid, name: undefined })).name).toBe(
      DEFAULT_PIPELINE_FILE_NAME,
    );
    expect(parsePipelineFile(JSON.stringify({ ...valid, name: "  " })).name).toBe(
      DEFAULT_PIPELINE_FILE_NAME,
    );
  });
});

describe("readFileText", () => {
  it("reads the file contents as text", async () => {
    const file = new File(['{"a":1}'], "pipeline.json", { type: "application/json" });

    await expect(readFileText(file)).resolves.toBe('{"a":1}');
  });
});
