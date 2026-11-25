import { describe, it, expect } from "vitest";
import { readdirSync } from "node:fs";
import { resolve } from "node:path";

describe("Blockly media", () => {
  it("ships every file from blockly/media in public/blockly-media", () => {
    const blocklyMedia = readdirSync(resolve(__dirname, "../node_modules/blockly/media")).sort();
    const publicMedia = readdirSync(resolve(__dirname, "../public/blockly-media")).sort();

    expect(publicMedia).toEqual(blocklyMedia);
  });
});
