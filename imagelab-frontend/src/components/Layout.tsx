import { useRef, useState } from "react";
import { useBlocklyWorkspace } from "../hooks/useBlocklyWorkspace";
import { usePipelineStore } from "../store/pipelineStore";
import { useImageDropAndPaste } from "../hooks/useImageUpload";
import { useDarkMode } from "../hooks/useDarkMode";
import Navbar from "./Navbar";
import Toolbar from "./Toolbar";
import Sidebar from "./Sidebar/Sidebar";
import PreviewPane from "./Preview/PreviewPane";
import InfoPane from "./InfoPane";
import { ErrorBoundary } from "./ErrorBoundary";
import { Upload } from "lucide-react";

export default function Layout() {
  const [isDark, toggleDark] = useDarkMode();
  const { containerRef, workspace } = useBlocklyWorkspace({ isDark });
  const { reset } = usePipelineStore();
  const [resetKey, setResetKey] = useState(0);
  const workspaceAreaRef = useRef<HTMLDivElement>(null);
  const { isDragging } = useImageDropAndPaste(workspaceAreaRef, workspace);

  const handleEditorReset = () => {
    setResetKey((prev) => prev + 1);
    reset();
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      <Navbar isDark={isDark} onToggleDark={toggleDark} />
      <Toolbar workspace={workspace} />
      <div className="flex flex-1 min-h-0">
        <Sidebar workspace={workspace} />
        <ErrorBoundary key={resetKey} onReset={handleEditorReset}>
          <div className="flex-1 flex min-w-0">
            <div className="flex-1 flex flex-col min-w-0 relative" ref={workspaceAreaRef}>
              <div ref={containerRef} className="flex-1" />
              <InfoPane />
              {isDragging && (
                <div className="drop-overlay">
                  <div className="drop-overlay__inner">
                    <Upload size={32} className="text-indigo-400 mb-2" />
                    <p className="text-sm font-medium text-gray-700">Drop image to load</p>
                  </div>
                </div>
              )}
            </div>
            <PreviewPane />
          </div>
        </ErrorBoundary>
      </div>
    </div>
  );
}
