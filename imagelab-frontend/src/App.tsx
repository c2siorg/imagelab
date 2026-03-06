import { useState, useCallback } from "react";
import Layout from "./components/Layout";
import LandingPage from "./components/LandingPage";

// Increment this version whenever the landing page content changes significantly
// to ensure all users (even those who checked "Don't show again") see the updates.
export const LANDING_VERSION = 1;
export const HIDE_LANDING_KEY = `hideLandingPage_v${LANDING_VERSION}`;

function getHideLanding(): boolean {
  try {
    return localStorage.getItem(HIDE_LANDING_KEY) === "true";
  } catch {
    return false; // fail open — show the landing page
  }
}

function setHideLanding(): void {
  try {
    localStorage.setItem(HIDE_LANDING_KEY, "true");
  } catch {
    // quota exceeded or storage disabled — silently ignore
  }
}

export default function App() {
  const [showLanding, setShowLanding] = useState(() => !getHideLanding());

  const handleStart = useCallback((dontShowAgain: boolean) => {
    if (dontShowAgain) {
      setHideLanding();
    }
    setShowLanding(false);
  }, []);

  return showLanding ? <LandingPage onStart={handleStart} /> : <Layout />;
}
