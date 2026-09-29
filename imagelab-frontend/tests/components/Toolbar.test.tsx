/**
 * @vitest-environment jsdom
 */
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import * as Blockly from "blockly";
import { setupBlocklyFields } from "../../src/blockly-setup";
import { registerAllBlocks } from "../../src/blocks/definitions";
import Toolbar from "../../src/components/Toolbar";
import { usePipelineStore } from "../../src/store/pipelineStore";
import { PIPELINE_FILE_SCHEMA_VERSION, serializePipelineFile } from "../../src/utils/pipelineFile";

const EXPORT_TITLE = "Export Pipeline (.json)";
const IMPORT_TITLE = "Import Pipeline (.json)";
const DATA_URL_PREFIX = "data:application/json;charset=utf-8,";

let workspace: Blockly.Workspace;

function toolbarWorkspace(): Blockly.WorkspaceSvg {
  // Toolbar only calls Workspace methods for export/import, so a headless workspace is enough.
  return workspace as unknown as Blockly.WorkspaceSvg;
}

function addBlurBlock(ws: Blockly.Workspace, id: string, width: number): void {
  const block = ws.newBlock("blurring_applygaussianblur", id);
  block.setFieldValue(width, "widthSize");
  block.moveBy(10, 20);
}

function pipelineFile(ws: Blockly.Workspace, name: string): File {
  const text = serializePipelineFile({
    schemaVersion: PIPELINE_FILE_SCHEMA_VERSION,
    name,
    workspace: Blockly.serialization.workspaces.save(ws),
  });
  return new File([text], `${name}.json`, { type: "application/json" });
}

function importFile(file: File): void {
  const input = screen.getByLabelText("Import pipeline file");
  fireEvent.change(input, { target: { files: [file] } });
}

beforeAll(() => {
  setupBlocklyFields();
  registerAllBlocks();
});

beforeEach(() => {
  usePipelineStore.getState().reset();
  workspace = new Blockly.Workspace();
});

afterEach(() => {
  cleanup();
  workspace.dispose();
  vi.restoreAllMocks();
});

describe("Toolbar pipeline export", () => {
  it("downloads the current workspace as a versioned .json file", () => {
    addBlurBlock(workspace, "blur-1", 9);
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    render(<Toolbar workspace={toolbarWorkspace()} />);

    fireEvent.click(screen.getByTitle(EXPORT_TITLE));

    expect(click).toHaveBeenCalledTimes(1);
    const link = click.mock.instances[0] as unknown as HTMLAnchorElement;
    expect(link.download).toBe("pipeline.json");
    expect(link.href.startsWith(DATA_URL_PREFIX)).toBe(true);
    const payload = JSON.parse(decodeURIComponent(link.href.slice(DATA_URL_PREFIX.length)));
    expect(payload).toEqual({
      schemaVersion: PIPELINE_FILE_SCHEMA_VERSION,
      name: "pipeline",
      workspace: Blockly.serialization.workspaces.save(workspace),
    });
    expect(payload.workspace.blocks.blocks[0]).toMatchObject({
      type: "blurring_applygaussianblur",
      id: "blur-1",
      x: 10,
      y: 20,
      fields: { widthSize: 9 },
    });
  });

  it("names the file after the open pipeline", () => {
    usePipelineStore.setState({ currentPipelineName: "Soft Blur" });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    render(<Toolbar workspace={toolbarWorkspace()} />);

    fireEvent.click(screen.getByTitle(EXPORT_TITLE));

    const link = click.mock.instances[0] as unknown as HTMLAnchorElement;
    expect(link.download).toBe("soft-blur.json");
    const payload = JSON.parse(decodeURIComponent(link.href.slice(DATA_URL_PREFIX.length)));
    expect(payload.name).toBe("Soft Blur");
  });
});

describe("Toolbar pipeline import", () => {
  it("loads an exported file into an empty workspace and detaches the server pipeline", async () => {
    const source = new Blockly.Workspace();
    addBlurBlock(source, "blur-1", 11);
    const file = pipelineFile(source, "Soft Blur");
    source.dispose();
    usePipelineStore.getState().setCurrentPipeline("pipe-1", "Old", 3);
    render(<Toolbar workspace={toolbarWorkspace()} />);

    importFile(file);

    await waitFor(() => expect(workspace.getAllBlocks(false)).toHaveLength(1));
    const block = workspace.getBlockById("blur-1")!;
    expect(block.getFieldValue("widthSize")).toBe(11);
    expect(block.getRelativeToSurfaceXY()).toEqual(new Blockly.utils.Coordinate(10, 20));
    expect(usePipelineStore.getState().currentPipelineId).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("migrates a legacy affine block in the imported file", async () => {
    const text = JSON.stringify({
      schemaVersion: PIPELINE_FILE_SCHEMA_VERSION,
      name: "Legacy",
      workspace: {
        blocks: {
          languageVersion: 0,
          blocks: [
            {
              type: "geometric_affineimage",
              id: "affine-1",
              fields: { translate_x: 20, translate_y: 5 },
            },
          ],
        },
      },
    });
    render(<Toolbar workspace={toolbarWorkspace()} />);

    importFile(new File([text], "legacy.json", { type: "application/json" }));

    await waitFor(() => expect(workspace.getBlockById("affine-1")).not.toBeNull());
    const affine = workspace.getBlockById("affine-1")!;
    expect(affine.getFieldValue("src_x1")).toBe(0);
    expect(affine.getFieldValue("dst_x1")).toBe(20);
    expect(affine.getFieldValue("dst_y1")).toBe(5);
    expect(affine.getFieldValue("dst_x2")).toBe(120);
    expect(affine.getFieldValue("dst_y2")).toBe(5);
    expect(affine.getFieldValue("dst_x3")).toBe(20);
    expect(affine.getFieldValue("dst_y3")).toBe(105);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("asks before replacing existing blocks and keeps them on cancel", async () => {
    addBlurBlock(workspace, "existing", 3);
    const source = new Blockly.Workspace();
    addBlurBlock(source, "incoming", 5);
    const file = pipelineFile(source, "Incoming");
    source.dispose();
    render(<Toolbar workspace={toolbarWorkspace()} />);

    importFile(file);
    await screen.findByText(/Importing "Incoming" will replace the blocks/);
    fireEvent.click(screen.getByText("Cancel"));

    expect(workspace.getBlockById("existing")).not.toBeNull();
    expect(workspace.getBlockById("incoming")).toBeNull();

    importFile(file);
    await screen.findByText(/Importing "Incoming" will replace the blocks/);
    fireEvent.click(screen.getByText("Replace"));

    await waitFor(() => expect(workspace.getBlockById("incoming")).not.toBeNull());
    expect(workspace.getBlockById("existing")).toBeNull();
    expect(workspace.getAllBlocks(false)).toHaveLength(1);
  });

  it("shows a readable error for a file that is not a pipeline export", async () => {
    render(<Toolbar workspace={toolbarWorkspace()} />);

    importFile(new File(["{ not json"], "broken.json", { type: "application/json" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("The selected file is not valid JSON.");
    expect(workspace.getAllBlocks(false)).toHaveLength(0);

    fireEvent.click(screen.getByLabelText("Dismiss error"));
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("rejects an unsupported schema version", async () => {
    render(<Toolbar workspace={toolbarWorkspace()} />);
    const text = JSON.stringify({ schemaVersion: 99, name: "Future", workspace: {} });

    importFile(new File([text], "future.json", { type: "application/json" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Unsupported pipeline file version 99");
  });

  it("keeps the current blocks when the file cannot be loaded into Blockly", async () => {
    addBlurBlock(workspace, "existing", 3);
    const before = Blockly.serialization.workspaces.save(workspace);
    const text = JSON.stringify({
      schemaVersion: PIPELINE_FILE_SCHEMA_VERSION,
      name: "Broken",
      workspace: { blocks: { languageVersion: 0, blocks: [{ type: "not_a_real_block" }] } },
    });
    render(<Toolbar workspace={toolbarWorkspace()} />);

    importFile(new File([text], "broken.json", { type: "application/json" }));
    await screen.findByText(/Importing "Broken" will replace the blocks/);
    fireEvent.click(screen.getByText("Replace"));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain('Could not load "Broken"');
    expect(Blockly.serialization.workspaces.save(workspace)).toEqual(before);
  });

  it("disables export and import in read-only shared mode", () => {
    usePipelineStore.setState({ isReadOnly: true });
    render(<Toolbar workspace={toolbarWorkspace()} />);

    expect(screen.getByTitle(EXPORT_TITLE)).toHaveProperty("disabled", true);
    expect(screen.getByTitle(IMPORT_TITLE)).toHaveProperty("disabled", true);
  });
});
