import { render, screen, fireEvent } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";
import App, { HIDE_LANDING_KEY } from "./App";

// Need to mock the Layout component as it likely uses browser/Blockly specific stuff
vi.mock("./components/Layout", () => {
  return {
    default: () => <div data-testid="mock-layout">Main Workspace</div>,
  };
});

describe("App / Landing Page routing", () => {
  beforeEach(() => {
    try {
      localStorage.clear();
    } catch {
      // gracefully ignore if mocked localStorage clear fails
    }
  });

  test("shows landing page when localStorage key is absent", () => {
    render(<App />);
    expect(screen.getByText(/Enter Workspace/i)).toBeInTheDocument();
    expect(screen.queryByTestId("mock-layout")).not.toBeInTheDocument();
  });

  test("skips landing page when hideLandingPage is set", () => {
    localStorage.setItem(HIDE_LANDING_KEY, "true");
    render(<App />);
    expect(screen.queryByText(/Enter Workspace/i)).not.toBeInTheDocument();
    expect(screen.getByTestId("mock-layout")).toBeInTheDocument();
  });

  test('sets localStorage when "Don\'t show again" is checked', () => {
    render(<App />);
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: /Enter Workspace/i }));

    expect(localStorage.getItem(HIDE_LANDING_KEY)).toBe("true");
    expect(screen.getByTestId("mock-layout")).toBeInTheDocument();
  });

  test("does NOT set localStorage when checkbox is unchecked", () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /Enter Workspace/i }));

    expect(localStorage.getItem(HIDE_LANDING_KEY)).toBeNull();
    expect(screen.getByTestId("mock-layout")).toBeInTheDocument();
  });

  test("shows landing page gracefully when localStorage.getItem throws", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("SecurityError");
    });
    render(<App />);
    expect(screen.getByText(/Enter Workspace/i)).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  test("still navigates to workspace when localStorage.setItem throws", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("QuotaExceededError");
    });
    render(<App />);
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: /Enter Workspace/i }));
    expect(screen.getByTestId("mock-layout")).toBeInTheDocument();
    vi.restoreAllMocks();
  });
});
