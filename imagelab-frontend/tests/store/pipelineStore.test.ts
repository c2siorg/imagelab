import { beforeEach, describe, expect, it, vi } from "vitest";
import { usePipelineStore } from "../../src/store/pipelineStore";

beforeEach(() => {
  usePipelineStore.getState().reset();
});

describe("registerImageReset", () => {
  it("calls all registered listeners when clearImage is invoked", () => {
    const fn1 = vi.fn();
    const fn2 = vi.fn();

    usePipelineStore.getState().registerImageReset(fn1);
    usePipelineStore.getState().registerImageReset(fn2);
    usePipelineStore.getState().clearImage();

    expect(fn1).toHaveBeenCalledOnce();
    expect(fn2).toHaveBeenCalledOnce();
  });

  it("does not call the same function twice when registered once", () => {
    const fn = vi.fn();

    usePipelineStore.getState().registerImageReset(fn);
    usePipelineStore.getState().clearImage();

    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("returned unsubscribe removes the listener so it is not called on clearImage", () => {
    const fn1 = vi.fn();
    const fn2 = vi.fn();

    const unregister = usePipelineStore.getState().registerImageReset(fn1);
    usePipelineStore.getState().registerImageReset(fn2);

    unregister();
    usePipelineStore.getState().clearImage();

    expect(fn1).not.toHaveBeenCalled();
    expect(fn2).toHaveBeenCalledOnce();
  });

  it("listeners persist across multiple clearImage calls until unsubscribed", () => {
    const fn = vi.fn();

    usePipelineStore.getState().registerImageReset(fn);
    usePipelineStore.getState().clearImage();
    usePipelineStore.getState().clearImage();

    expect(fn).toHaveBeenCalledTimes(2);
  });
});

describe("reset", () => {
  it("clears all listeners so clearImage does not call them after reset", () => {
    const fn = vi.fn();

    usePipelineStore.getState().registerImageReset(fn);
    usePipelineStore.getState().reset();
    usePipelineStore.getState().clearImage();

    expect(fn).not.toHaveBeenCalled();
  });

  it("allows fresh listeners registered after reset to fire normally", () => {
    const stale = vi.fn();
    const fresh = vi.fn();

    usePipelineStore.getState().registerImageReset(stale);
    usePipelineStore.getState().reset();
    usePipelineStore.getState().registerImageReset(fresh);
    usePipelineStore.getState().clearImage();

    expect(stale).not.toHaveBeenCalled();
    expect(fresh).toHaveBeenCalledOnce();
  });
});

describe("clearImage", () => {
  it("resets image-related state fields", () => {
    usePipelineStore.getState().setOriginalImage("base64data", "png");
    usePipelineStore.getState().setProcessedImage("processed");
    usePipelineStore.getState().setError("some error", 2);

    usePipelineStore.getState().clearImage();

    const state = usePipelineStore.getState();
    expect(state.originalImage).toBeNull();
    expect(state.processedImage).toBeNull();
    expect(state.error).toBeNull();
    expect(state.errorStep).toBeNull();
  });
});
