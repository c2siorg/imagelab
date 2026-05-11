import * as Blockly from "blockly";
import { registerReadImageExtension } from "../extensions/readImageExtension";
import { basicBlocks } from "./basic.blocks";
import { geometricBlocks } from "./geometric.blocks";
import { conversionsBlocks } from "./conversions.blocks";
import { drawingBlocks } from "./drawing.blocks";
import { blurringBlocks } from "./blurring.blocks";
import { filteringBlocks } from "./filtering.blocks";
import { thresholdingBlocks } from "./thresholding.blocks";
import { sobelDerivativesBlocks } from "./sobel-derivatives.blocks";
import { transformationBlocks } from "./transformation.blocks";
import { augmentationBlocks } from "./augmentation.blocks";
import { segmentationBlocks } from "./segmentation.blocks";

function registerOddKernelValidator() {
  if (Blockly.Extensions.isRegistered("odd_kernel_validator")) return;

  Blockly.Extensions.register("odd_kernel_validator", function (this: Blockly.Block) {
    const field = this.getField("kernelSize");
    if (!field) {
      console.warn(
        `[odd_kernel_validator] Field "kernelSize" not found on block type "${this.type}". Validator not applied.`,
      );
      return;
    }

    field.setValidator((newValue: number): number | null => {
      if (!Number.isFinite(newValue)) return null;

      let normalized = Math.max(1, Math.round(newValue));
      if (normalized % 2 === 0) normalized += 1;
      return normalized;
    });
  });
}

/**
 * Store default values per block type for restore-to-defaults functionality.
 * Maps blockType -> fieldName -> defaultValue
 */
const blockDefaults = new Map<string, Record<string, unknown>>();

type ContextMenuItem = {
  enabled?: boolean;
  text: string;
  callback?: (...args: unknown[]) => void;
};

/**
 * Extract default field values from a block's JSON definition.
 */
function extractDefaults(blockDef: unknown): Record<string, unknown> {
  const defaults: Record<string, unknown> = {};

  // Iterate through args0, args1, args2, etc.
  if (typeof blockDef !== "object" || blockDef === null) return defaults;
  const bd = blockDef as Record<string, unknown>;
  const argsKeys = Object.keys(bd).filter((k) => k.startsWith("args"));
  argsKeys.forEach((argsKey) => {
    const args = bd[argsKey] as unknown;
    if (!Array.isArray(args)) return;

    (args as unknown[]).forEach((arg: unknown) => {
      if (!arg || typeof arg !== "object") return;
      const a = arg as Record<string, unknown>;
      if (!a.type || !a.name) return;

      const fieldType = String(a.type);
      let defaultValue: unknown;

      // Extract default value based on field type
      if (fieldType === "field_number") {
        defaultValue = a["value"];
      } else if (fieldType === "field_dropdown") {
        const v = a["value"];
        if (v !== undefined) {
          defaultValue = v;
        } else {
          const opts = a["options"];
          if (Array.isArray(opts) && opts.length > 0) {
            const first = opts[0];
            if (Array.isArray(first) && first.length > 1) defaultValue = first[1];
            else if (typeof first === "string") defaultValue = first;
          }
        }
      } else if (fieldType === "field_colour" || fieldType === "field_color") {
        defaultValue = a["colour"] ?? a["color"] ?? a["value"];
      } else if (fieldType === "field_input") {
        defaultValue = a["text"] ?? a["value"] ?? "";
      } else if (fieldType === "field_checkbox") {
        defaultValue = a["checked"] ?? a["value"] ?? false;
      } else if (fieldType === "field_variable") {
        defaultValue = a["variable"]; // variable block references
      } else if (fieldType === "field_label" || fieldType === "field_label_serializable") {
        // Labels typically don't need restoration
        return;
      } else {
        // Fallback for other field types
        defaultValue = a["value"];
      }

      if (defaultValue !== undefined && defaultValue !== null) {
        defaults[String(a["name"])] = defaultValue;
      }
    });
  });

  return defaults;
}

export function registerAllBlocks() {
  registerReadImageExtension();
  registerOddKernelValidator();

  const allBlockDefs = [
    ...basicBlocks,
    ...geometricBlocks,
    ...conversionsBlocks,
    ...drawingBlocks,
    ...blurringBlocks,
    ...filteringBlocks,
    ...thresholdingBlocks,
    ...sobelDerivativesBlocks,
    ...transformationBlocks,
    ...augmentationBlocks,
    ...segmentationBlocks,
  ];

  // Pre-compute defaults for each block type
  allBlockDefs.forEach((def: unknown) => {
    const d = def as Record<string, unknown>;
    if (!d.type) return;
    blockDefaults.set(String(d.type), extractDefaults(d));
  });

  Blockly.defineBlocksWithJsonArray(allBlockDefs);

  // Register a global extension that handles context menu for all blocks
  if (!Blockly.Extensions.isRegistered("restore_defaults_menu")) {
    Blockly.Extensions.register("restore_defaults_menu", function (this: Blockly.Block) {
      const defaults = blockDefaults.get(this.type);
      if (!defaults || Object.keys(defaults).length === 0) return;

      // Wrap the existing customContextMenu if it exists
      const originalContextMenu =
        (this as unknown as { customContextMenu?: unknown }).customContextMenu ?? null;

      (
        this as unknown as { customContextMenu?: (options: ContextMenuItem[]) => void }
      ).customContextMenu = function (options: ContextMenuItem[]) {
        // Call original if it exists
        if (originalContextMenu && typeof originalContextMenu === "function") {
          (originalContextMenu as (options: ContextMenuItem[]) => void).call(this, options);
        }

        options.push({
          enabled: true,
          text: "Restore defaults",
          callback: () => {
            Object.entries(defaults).forEach(([fieldName, defaultVal]) => {
              try {
                (this as Blockly.Block).setFieldValue(
                  defaultVal as string | number,
                  String(fieldName),
                );
              } catch {
                // Silently ignore if field can't be set
              }
            });
          },
        });
      };
    });
  }

  // Attach the restore_defaults_menu extension to all block definitions
  allBlockDefs.forEach((def: unknown) => {
    const d = def as Record<string, unknown>;
    if (!d.extensions) {
      d.extensions = [];
    } else if (typeof d.extensions === "string") {
      d.extensions = [d.extensions];
    }
    if (!(d.extensions as unknown[]).includes("restore_defaults_menu")) {
      (d.extensions as unknown[]).push("restore_defaults_menu");
    }
  });

  // Re-define blocks with the updated extensions
  Blockly.defineBlocksWithJsonArray(allBlockDefs);
}
