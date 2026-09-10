import { useState } from "react";
import { LandingScreen } from "./components/LandingScreen";
import Layout from "./components/Layout";
import { getShareTokenFromUrl } from "./utils/shareUrl";

const STORAGE_KEY = "imagelab:skipLanding";

function getShouldShowLanding(): boolean {
  if (getShareTokenFromUrl()) {
    return false;
  }
  try {
    return localStorage.getItem(STORAGE_KEY) !== "true";
  } catch {
    return true;
  }
}

export default function App() {
  const [showLanding, setShowLanding] = useState(getShouldShowLanding);
  const shareToken = getShareTokenFromUrl();

  if (showLanding) {
    return <LandingScreen onStart={() => setShowLanding(false)} />;
  }

  return <Layout shareToken={shareToken} />;
}
