import { useState } from "react";
import { LandingScreen } from "./components/LandingScreen";
import Layout from "./components/Layout";

const STORAGE_KEY = "imagelab:skipLanding";

function getShouldShowLanding(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) !== "true";
  } catch {
    return true;
  }
}

export default function App() {
  const [showLanding, setShowLanding] = useState(getShouldShowLanding);

  if (showLanding) {
    return <LandingScreen onStart={() => setShowLanding(false)} />;
  }

  return <Layout />;
}
