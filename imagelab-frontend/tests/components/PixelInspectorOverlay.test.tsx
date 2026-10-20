/**
 * @vitest-environment jsdom
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render } from "@testing-library/react";
import PixelInspectorOverlay from "../../src/components/Preview/PixelInspectorOverlay";

describe("PixelInspectorOverlay Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("does not render when active is false", () => {
    const imgRef = { current: document.createElement("img") };
    const containerRef = { current: document.createElement("div") };

    const { container } = render(
      <PixelInspectorOverlay imageRef={imgRef} containerRef={containerRef} active={false} />,
    );

    expect(container.firstChild).toBeNull();
  });

  it("attaches pointermove listener to container when active is true", () => {
    const container = document.createElement("div");
    const addEventListenerSpy = vi.spyOn(container, "addEventListener");

    const imgRef = { current: document.createElement("img") };
    const containerRef = { current: container };

    render(<PixelInspectorOverlay imageRef={imgRef} containerRef={containerRef} active={true} />);

    expect(addEventListenerSpy).toHaveBeenCalledWith("pointermove", expect.any(Function));
    expect(addEventListenerSpy).toHaveBeenCalledWith("pointerleave", expect.any(Function));
  });
});
