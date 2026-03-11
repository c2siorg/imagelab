import { useState } from "react";
import { useBlocklyWorkspace } from "../hooks/useBlocklyWorkspace";
import { usePipelineStore } from "../store/pipelineStore";
import Navbar from "./Navbar";
import Toolbar from "./Toolbar";
import Sidebar from "./Sidebar/Sidebar";
import PreviewPane from "./Preview/PreviewPane";
import InfoPane from "./InfoPane";
import StepPreviewList from "./Preview/StepPreviewList";
import { ErrorBoundary } from "./ErrorBoundary";

export default function Layout() {
  const { containerRef, workspace } = useBlocklyWorkspace();
  const { reset, showStepPreviews, intermediates } = usePipelineStore();
  const [resetKey, setResetKey] = useState(0);

  const handleEditorReset = () => {
    setResetKey((prev) => prev + 1);
    reset();
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
            {showStepPreviews && intermediates && intermediates.length > 0 && (
              <div className="w-60 flex-shrink-0 border-l border-gray-200 bg-white flex flex-col min-h-0">
                <div className="px-3 py-2 border-b border-gray-100 flex-shrink-0">
                  <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                    Step Preview
                  </p>
                  <p className="text-[10px] text-gray-400">{intermediates.length} steps</p>
                </div>
                <div className="flex-1 overflow-y-auto">
                  <StepPreviewList steps={intermediates} />
                </div>
              </div>
            )}
          </div>
        </ErrorBoundary>
      </div>
    </div>
  );
}
