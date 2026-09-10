import * as Blockly from "blockly";

export const controlFlowBlocks = [
  {
    type: "macro_blend",
    message0: "Parallel Blend  Alpha %1",
    args0: [
      {
        type: "field_number",
        name: "alpha",
        value: 0.5,
        min: 0.0,
        max: 1.0,
        precision: 0.01,
      },
    ],
    message1: "Branch 1 (Op 1) %1",
    args1: [
      {
        type: "input_statement",
        name: "OP1",
      },
    ],
    message2: "Branch 2 (Op 2) %1",
    args2: [
      {
        type: "input_statement",
        name: "OP2",
      },
    ],
    previousStatement: null,
    nextStatement: null,
    colour: "#7058a3",
    tooltip: "Parallel Blend Macro (Masking)",
    helpUrl: "",
  },
  {
    type: "macro_if_else",
    message0: "If %1 %2 %3",
    args0: [
      {
        type: "field_dropdown",
        name: "metric",
        options: [
          ["Mean Brightness", "mean_brightness"],
          ["Width", "width"],
          ["Height", "height"],
        ],
      },
      {
        type: "field_dropdown",
        name: "comparator",
        options: [
          [">", ">"],
          ["<", "<"],
          ["==", "=="],
        ],
      },
      {
        type: "field_number",
        name: "threshold",
        value: 128,
      },
    ],
    message1: "Then (If Branch) %1",
    args1: [
      {
        type: "input_statement",
        name: "IF_BRANCH",
      },
    ],
    message2: "Else (Else Branch) %1",
    args2: [
      {
        type: "input_statement",
        name: "ELSE_BRANCH",
      },
    ],
    previousStatement: null,
    nextStatement: null,
    colour: "#7058a3",
    tooltip: "Conditional (If/Else) Macro",
    helpUrl: "",
  },
];

type ContextMenuItem = {
  text: string;
  enabled?: boolean;
  callback?: () => void;
};

export function registerControlFlowBlocks(): void {
  Blockly.Blocks["macro_blend"] = {
    init: function (this: Blockly.Block) {
      this.jsonInit(controlFlowBlocks[0]);
    },
    customContextMenu: function (this: Blockly.Block, options: ContextMenuItem[]) {
      for (const option of options) {
        const text = (typeof option.text === "string" ? option.text : "").toLowerCase();
        // Only disable the "edit" option, allow delete and duplicate
        if (text.includes("edit")) {
          option.enabled = false;
        }
      }
    },
  };

  Blockly.Blocks["macro_if_else"] = {
    init: function (this: Blockly.Block) {
      this.jsonInit(controlFlowBlocks[1]);
    },
    customContextMenu: function (this: Blockly.Block, options: ContextMenuItem[]) {
      for (const option of options) {
        const text = (typeof option.text === "string" ? option.text : "").toLowerCase();
        // Only disable the "edit" option, allow delete and duplicate
        if (text.includes("edit")) {
          option.enabled = false;
        }
      }
    },
  };
}
