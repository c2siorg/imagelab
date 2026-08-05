/**
 * @vitest-environment jsdom
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type * as Blockly from "blockly";
import CreateMacroModal from "../../src/components/modals/CreateMacroModal";
import { useMacroStore } from "../../src/store/useMacroStore";

function createMockBlock(
  id: string,
  type: string,
  paramName?: string,
  paramVal?: unknown,
  next?: unknown,
) {
  const fields = paramName ? [{ name: paramName, getValue: () => paramVal }] : [];
  return {
    id,
    type,
    inputList: [
      {
        fieldRow: fields,
        type: 0,
        connection: { targetBlock: () => null },
      },
    ],
    getNextBlock: () => next || null,
  } as unknown as Blockly.Block;
}

describe("CreateMacroModal Component", () => {
  beforeEach(() => {
    useMacroStore.setState({
      macros: [],
      selectedMacro: null,
      isLoading: false,
      error: null,
    });
    vi.restoreAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders form fields and exposed parameter checkboxes", () => {
    const b2 = createMockBlock("b2", "canny", "threshold", 100);
    const b1 = createMockBlock("b1", "blur", "kernel", 5, b2);
    const selectedBlocks = [b1, b2];

    render(<CreateMacroModal selectedBlocks={selectedBlocks} onClose={vi.fn()} />);

    expect(screen.getByText("Create New Macro")).toBeTruthy();
    expect(screen.getByLabelText(/Macro Name \*/i)).toBeTruthy();
    expect(screen.getByLabelText(/Description \(Optional\)/i)).toBeTruthy();

    expect(screen.getByText("kernel")).toBeTruthy();
    expect(screen.getByText("threshold")).toBeTruthy();
  });

  it("toggles parameter checkboxes and submits graph JSON with exposed params", async () => {
    const b2 = createMockBlock("b2", "canny", "threshold", 100);
    const b1 = createMockBlock("b1", "blur", "kernel", 5, b2);
    const selectedBlocks = [b1, b2];

    const addMacroSpy = vi.fn().mockResolvedValue({ id: "macro-1" });
    useMacroStore.setState({ addMacro: addMacroSpy });

    const onClose = vi.fn();
    const { container } = render(
      <CreateMacroModal selectedBlocks={selectedBlocks} onClose={onClose} />,
    );

    const nameInput = screen.getByLabelText(/Macro Name \*/i);
    fireEvent.change(nameInput, { target: { value: "My Edge Macro" } });

    const thresholdCheckbox = container.querySelector(
      "#param-b2\\:threshold",
    ) as HTMLInputElement;
    expect(thresholdCheckbox).toBeTruthy();
    fireEvent.click(thresholdCheckbox);

    const submitBtn = screen.getByRole("button", { name: "Create Macro" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(addMacroSpy).toHaveBeenCalledTimes(1);
    });

    expect(addMacroSpy).toHaveBeenCalledWith({
      name: "My Edge Macro",
      description: undefined,
      pipeline_json: {
        nodes: [
          { id: "b1", type: "blur", op: "blur", params: { kernel: 5 } },
          { id: "b2", type: "canny", op: "canny", params: { threshold: 100 } },
        ],
        edges: [{ from: "b1", to: "b2" }],
        exposed_params: [
          {
            blockId: "b1",
            blockType: "blur",
            paramName: "kernel",
            label: "kernel (blur)",
            defaultValue: 5,
          },
        ],
      },
      workspace_json: { block_ids: ["b1", "b2"] },
    });

    expect(onClose).toHaveBeenCalled();
  });

  it("displays error banner when submission fails", async () => {
    const b2 = createMockBlock("b2", "canny", "threshold", 100);
    const b1 = createMockBlock("b1", "blur", "kernel", 5, b2);
    const selectedBlocks = [b1, b2];

    const addMacroSpy = vi.fn().mockRejectedValue(new Error("Graph cycle detected"));
    useMacroStore.setState({ addMacro: addMacroSpy });

    render(<CreateMacroModal selectedBlocks={selectedBlocks} onClose={vi.fn()} />);

    const nameInput = screen.getByLabelText(/Macro Name \*/i);
    fireEvent.change(nameInput, { target: { value: "Invalid Macro" } });

    const submitBtn = screen.getByRole("button", { name: "Create Macro" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByTestId("error-banner")).toBeTruthy();
    });

    expect(screen.getByText("Graph cycle detected")).toBeTruthy();
  });
});
