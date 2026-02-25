import { useState } from "react";
import { useBlocklyWorkspace } from "../hooks/useBlocklyWorkspace";
import Navbar from "./Navbar";
import Toolbar from "./Toolbar";
import Sidebar from "./Sidebar/Sidebar";
import PreviewPane from "./Preview/PreviewPane";
import InfoPane from "./InfoPane";
import { ErrorBoundary } from "./ErrorBoundary";

export default function Layout() {
  const { containerRef, workspace } = useBlocklyWorkspace();
  const [resetKey, setResetKey] = useState(0);

  const handleEditorReset = () => {
    setResetKey((prev) => prev + 1);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Navbar />
      <Toolbar workspace={workspace} />
      <div className="flex flex-1 min-h-0">
        <Sidebar workspace={workspace} />
        <ErrorBoundary key={resetKey} onReset={handleEditorReset}>
          <div className="flex-1 flex min-w-0">
            <div className="flex-1 flex flex-col min-w-0">
              <div ref={containerRef} className="flex-1" />
              <InfoPane />
            </div>
            <PreviewPane />
          </div>
        </ErrorBoundary>
      </div>
    </div>
  );
}
