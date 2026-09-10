/**
 * Centralized utilities for handling exposed macro parameter field keys.
 * Ensures consistent formatting and parsing of field keys across the application.
 */

/**
 * Formats an exposed parameter field key using the strict double-underscore delimiter.
 * @param blockId - The ID of the block within the macro graph
 * @param paramName - The name of the parameter to expose
 * @returns A formatted field key in the format `${blockId}__${paramName}`
 */
export function formatExposedFieldKey(blockId: string, paramName: string): string {
  return `${blockId}__${paramName}`;
}

/**
 * Parses an exposed parameter field key back into its components.
 * Safely handles parameter names that may contain underscores or double-underscores.
 * @param fieldKey - The field key to parse (expected format: `${blockId}__${paramName}`)
 * @returns An object with blockId and paramName, or null if the key is invalid
 */
export function parseExposedFieldKey(
  fieldKey: string,
): { blockId: string; paramName: string } | null {
  const parts = fieldKey.split("__");
  if (parts.length < 2) return null;
  const blockId = parts[0];
  const paramName = parts.slice(1).join("__");
  return { blockId, paramName };
}

/**
 * Cleans any legacy prefixes from field labels (e.g., Blockly's internal `|PB=` prefix).
 * Ensures human-readable labels don't leak internal serialization details.
 * @param label - The label to clean
 * @returns The cleaned label without legacy prefixes
 */
export function cleanFieldLabel(label: string): string {
  if (!label) return "";

  // 1. Remove legacy |PB= prefix if present
  // Match |PB= followed by any characters until | or __ (double underscore)
  let cleaned = label.replace(/\|PB=[^|_]*/, "");

  // 2. If label contains internal double-underscore (e.g., "T6_iMF|-Nulf...__clipLimit")
  // Extract ONLY the actual parameter name after the double-underscore!
  if (cleaned.includes("__")) {
    const parts = cleaned.split("__");
    cleaned = parts[parts.length - 1]; // Takes "clipLimit"
  }

  return cleaned;
}
