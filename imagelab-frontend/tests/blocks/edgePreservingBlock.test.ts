import { describe, expect, it } from "vitest";
import { filteringBlocks } from "../../src/blocks/definitions/filtering.blocks";

describe("filtering_edgepreserving block definition", () => {
  const block = filteringBlocks.find((b) => b.type === "filtering_edgepreserving");

  it("should be defined in filteringBlocks array", () => {
    expect(block).toBeDefined();
  });

  it("should have correct style and statement connections", () => {
    expect(block?.style).toBe("filtering_style");
    expect(block?.previousStatement).toBeNull();
    expect(block?.nextStatement).toBeNull();
  });

  it("should have expected mode, sigma_s, and sigma_r fields", () => {
    const args = block?.args0 ?? [];
    const modeField = args.find((a) => (a as { name?: string }).name === "mode") as {
      type: string;
      options: [string, string][];
    };
    expect(modeField).toBeDefined();
    expect(modeField.type).toBe("field_dropdown");
    expect(modeField.options).toContainEqual(["Recursive Filter", "RECURS_FILTER"]);
    expect(modeField.options).toContainEqual(["Normalized Convolution", "NORMCONV_FILTER"]);

    const sigmaSField = args.find((a) => (a as { name?: string }).name === "sigma_s") as {
      type: string;
      value: number;
      min: number;
      max: number;
    };
    expect(sigmaSField).toBeDefined();
    expect(sigmaSField.value).toBe(60);
    expect(sigmaSField.min).toBe(1);
    expect(sigmaSField.max).toBe(200);

    const sigmaRField = args.find((a) => (a as { name?: string }).name === "sigma_r") as {
      type: string;
      value: number;
      min: number;
      max: number;
    };
    expect(sigmaRField).toBeDefined();
    expect(sigmaRField.value).toBe(0.4);
    expect(sigmaRField.min).toBe(0.05);
    expect(sigmaRField.max).toBe(1.0);
  });
});
