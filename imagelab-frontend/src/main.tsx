import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { registerAllBlocks } from "./blocks/definitions";
import App from "./App";
import { setupBlocklyFields } from "./blockly-setup";

// Register Blockly blocks once at startup, before any workspace is created.
setupBlocklyFields();
// Both the main workspace and the SVG preview workspace need registered blocks.
registerAllBlocks();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
