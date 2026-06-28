import { useState } from "react";
import { useBlocklyWorkspace } from "../hooks/useBlocklyWorkspace";
import { useShareFromUrl } from "../hooks/useShareFromUrl";
import { usePipelineStore } from "../store/pipelineStore";
import { useDarkMode } from "../hooks/useDarkMode";
import Navbar from "./Navbar";
import Toolbar from "./Toolbar";
import Sidebar from "./Sidebar/Sidebar";
import PreviewPane from "./Preview/PreviewPane";
import BottomPanel from "./BottomPanel";
import { ErrorBoundary } from "./ErrorBoundary";
import CameraCaptureModal from "./CameraCaptureModal";
import CloneSharedPipelineModal from "./CloneSharedPipelineModal";
import { Loader2 } from "lucide-react";

interface LayoutProps {
  shareToken?: string | null;
}

export default function Layout({ shareToken = null }: LayoutProps) {
  const [isDark, toggleDark] = useDarkMode();
  const { reset, isReadOnly, sharedPipelineName, sharedVersionNumber } = usePipelineStore();
  const { containerRef, workspace } = useBlocklyWorkspace({ isDark, readOnly: isReadOnly });
  const [resetKey, setResetKey] = useState(0);

  const {
    sharedPipeline,
    shareError,
    isResolvingShare,
    showClonePrompt,
    handleCloneComplete,
    dismissClonePrompt,
  } = useShareFromUrl({ workspace, shareToken });

  const handleEditorReset = () => {
    setResetKey((prev) => prev + 1);
    reset();
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      <Navbar isDark={isDark} onToggleDark={toggleDark} />
      {isReadOnly && sharedPipelineName && (
        <div className="px-4 py-2 text-xs text-amber-800 dark:text-amber-200 bg-amber-50 dark:bg-amber-950/40 border-b border-amber-200 dark:border-amber-900/50">
          Viewing shared pipeline <span className="font-semibold">{sharedPipelineName}</span> (v
          {sharedVersionNumber}) — read-only. Run the pipeline to preview results, but blocks cannot
          be edited.
        </div>
      )}
      {!isReadOnly && sharedPipelineName && (
        <div className="px-4 py-2 text-xs text-indigo-800 dark:text-indigo-200 bg-indigo-50 dark:bg-indigo-950/40 border-b border-indigo-200 dark:border-indigo-900/50">
          Editing shared pipeline <span className="font-semibold">{sharedPipelineName}</span> (from
          v{sharedVersionNumber}). Saving creates the next version in the same pipeline.
        </div>
      )}
      {shareError && (
        <div className="px-4 py-2 text-xs text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-950/30 border-b border-red-200 dark:border-red-900/50">
          {shareError}
        </div>
      )}
      <Toolbar workspace={workspace} />
      <div className="flex flex-1 min-h-0 relative">
        {isResolvingShare && (
          <div className="absolute inset-0 z-40 flex items-center justify-center bg-white/70 dark:bg-gray-900/70 backdrop-blur-xs">
            <div className="flex flex-col items-center gap-2 text-gray-600 dark:text-gray-300">
              <Loader2 size={24} className="animate-spin text-indigo-500" />
              <span className="text-xs font-medium">Loading shared pipeline...</span>
            </div>
          </div>
        )}
        {!isReadOnly && <Sidebar workspace={workspace} />}
        <ErrorBoundary key={resetKey} onReset={handleEditorReset}>
          <div className="flex-1 flex min-w-0">
            <div className="flex-1 flex flex-col min-w-0">
              <div ref={containerRef} className="flex-1" />
              <BottomPanel workspace={workspace} />
            </div>
            <PreviewPane />
          </div>
        </ErrorBoundary>
      </div>
      <CameraCaptureModal />
      {showClonePrompt && sharedPipeline && workspace && shareToken && (
        <CloneSharedPipelineModal
          workspace={workspace}
          shareToken={shareToken}
          sharedPipeline={sharedPipeline}
          onComplete={handleCloneComplete}
          onCancel={dismissClonePrompt}
        />
      )}
    </div>
  );
}
