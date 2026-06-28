import { useEffect, useState } from "react";
import * as Blockly from "blockly";
import { lookupShareToken } from "../api/persistence";
import type { SharedPipeline } from "../api/persistence";
import { usePipelineStore } from "../store/pipelineStore";
import { clearShareTokenFromUrl } from "../utils/shareUrl";
import { loadWorkspaceState } from "../utils/workspaceLoad";

interface UseShareFromUrlOptions {
  workspace: Blockly.WorkspaceSvg | null;
  shareToken: string | null;
}

export function useShareFromUrl({ workspace, shareToken }: UseShareFromUrlOptions) {
  const {
    setShareViewContext,
    setShareEditContext,
    setCurrentPipeline,
    setWorkspaceDirty,
    clearShareContext,
  } = usePipelineStore();
  const [sharedPipeline, setSharedPipeline] = useState<SharedPipeline | null>(null);
  const [shareError, setShareError] = useState<string | null>(null);
  const [isResolvingShare, setIsResolvingShare] = useState(Boolean(shareToken));
  const [showClonePrompt, setShowClonePrompt] = useState(false);

  useEffect(() => {
    if (!shareToken || !workspace) return;

    let cancelled = false;

    const resolveShare = async () => {
      setIsResolvingShare(true);
      setShareError(null);

      try {
        const shared = await lookupShareToken(shareToken);
        if (cancelled) return;

        if (shared.permission === "clone") {
          setSharedPipeline(shared);
          setShowClonePrompt(true);
          return;
        }

        loadWorkspaceState(workspace, shared.workspace_json);
        if (shared.permission === "edit") {
          setShareEditContext(
            shared.pipeline_id,
            shared.pipeline_name,
            shared.version_number,
            shareToken,
          );
        } else {
          setShareViewContext(shared.pipeline_name, shared.version_number, shareToken);
        }
        setWorkspaceDirty(false);
      } catch (err) {
        if (cancelled) return;
        setShareError(err instanceof Error ? err.message : "Invalid or expired share link");
        clearShareTokenFromUrl();
      } finally {
        if (!cancelled) {
          setIsResolvingShare(false);
        }
      }
    };

    void resolveShare();

    return () => {
      cancelled = true;
    };
  }, [shareToken, workspace, setShareEditContext, setShareViewContext, setWorkspaceDirty]);

  const handleCloneComplete = (clonedPipelineId: string, name: string) => {
    setShowClonePrompt(false);
    setSharedPipeline(null);
    clearShareContext();
    setCurrentPipeline(clonedPipelineId, name, 1);
    setWorkspaceDirty(false);
    clearShareTokenFromUrl();
  };

  const dismissClonePrompt = () => {
    setShowClonePrompt(false);
    setSharedPipeline(null);
    setShareError("Clone cancelled.");
    clearShareTokenFromUrl();
  };

  return {
    sharedPipeline,
    shareError,
    isResolvingShare,
    showClonePrompt,
    handleCloneComplete,
    dismissClonePrompt,
  };
}
