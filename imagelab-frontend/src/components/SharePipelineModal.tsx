import { useState, useEffect } from "react";
import * as Blockly from "blockly";
import { X, Copy, Check, Share2, Loader2, Link2 } from "lucide-react";
import { usePipelineStore } from "../store/pipelineStore";
import { createShareToken } from "../api/persistence";
import {
  buildShareUrl,
  computeShareExpiresAt,
  SHARE_EXPIRY_LABELS,
  type ShareExpiryOption,
} from "../utils/shareUrl";

interface SharePipelineModalProps {
  workspace: Blockly.WorkspaceSvg | null;
  onClose: () => void;
  onSaveFirst?: () => void;
}

export default function SharePipelineModal({
  workspace,
  onClose,
  onSaveFirst,
}: SharePipelineModalProps) {
  const {
    currentPipelineId,
    currentPipelineName,
    currentVersionNumber,
    workspaceDirty,
    isReadOnly,
  } = usePipelineStore();

  const [permission, setPermission] = useState<"view" | "clone" | "edit">("view");
  const [expiry, setExpiry] = useState<ShareExpiryOption>("none");
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const handleGenerate = async () => {
    if (!currentPipelineId || currentVersionNumber === null) return;

    setIsGenerating(true);
    setError(null);
    setShareUrl(null);
    setCopied(false);
    setCopyError(null);

    try {
      const { token } = await createShareToken(currentPipelineId, {
        version_number: currentVersionNumber,
        permission,
        expires_at: computeShareExpiresAt(expiry),
      });
      setShareUrl(buildShareUrl(token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate share link");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setCopyError(null);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopyError("Could not copy to clipboard. Please select and copy manually.");
    }
  };

  const needsSave = !currentPipelineId || currentVersionNumber === null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 backdrop-blur-xs"
      onClick={onClose}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Share Pipeline"
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden border border-gray-200 dark:border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <div className="flex items-center gap-2">
            <Share2 size={18} className="text-indigo-500" />
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
              Share Pipeline
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
            title="Close"
            aria-label="Close"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>

        <div className="p-5 space-y-5">
          {isReadOnly && (
            <div className="p-3 text-xs bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/50 text-amber-700 dark:text-amber-300 rounded-lg">
              Shared view-only pipelines cannot be re-shared.
            </div>
          )}

          {needsSave ? (
            <div className="space-y-3">
              <p className="text-xs text-gray-600 dark:text-gray-300">
                Save your pipeline first to generate a secure share link for a specific version.
              </p>
              {onSaveFirst && (
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onSaveFirst();
                  }}
                  className="w-full py-2 px-3 rounded-lg text-sm font-medium text-white bg-indigo-500 hover:bg-indigo-600 transition-colors"
                >
                  Save Pipeline First
                </button>
              )}
            </div>
          ) : (
            <>
              <div className="p-3 bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/50 rounded-lg">
                <p className="text-xs text-indigo-700 dark:text-indigo-300">
                  Sharing <span className="font-semibold">{currentPipelineName}</span> at{" "}
                  <span className="font-semibold">v{currentVersionNumber}</span>.
                  {workspaceDirty && (
                    <span className="block mt-1 text-amber-700 dark:text-amber-300">
                      You have unsaved changes. The link will point to the last saved version, not
                      your current edits.
                    </span>
                  )}
                </p>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wide">
                  Permission
                </p>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setPermission("view")}
                    className={`py-2 px-3 rounded-lg text-xs font-medium border transition-colors ${
                      permission === "view"
                        ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300"
                        : "border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                    }`}
                  >
                    View only
                  </button>
                  <button
                    type="button"
                    onClick={() => setPermission("clone")}
                    className={`py-2 px-3 rounded-lg text-xs font-medium border transition-colors ${
                      permission === "clone"
                        ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300"
                        : "border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                    }`}
                  >
                    Allow clone
                  </button>
                  <button
                    type="button"
                    onClick={() => setPermission("edit")}
                    className={`py-2 px-3 rounded-lg text-xs font-medium border transition-colors ${
                      permission === "edit"
                        ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300"
                        : "border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                    }`}
                  >
                    Allow edit
                  </button>
                </div>
                <p className="text-[11px] text-gray-400 dark:text-gray-500">
                  {permission === "view"
                    ? "Recipients can open this exact version read-only."
                    : permission === "clone"
                      ? "Recipients can duplicate this version into their own pipeline."
                      : "Recipients can add new versions to this same pipeline."}
                </p>
              </div>

              <div className="space-y-2">
                <label
                  htmlFor="share-expiry"
                  className="text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wide"
                >
                  Link Expiry
                </label>
                <select
                  id="share-expiry"
                  value={expiry}
                  onChange={(e) => setExpiry(e.target.value as ShareExpiryOption)}
                  className="w-full text-xs bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                  disabled={isGenerating}
                >
                  {(Object.keys(SHARE_EXPIRY_LABELS) as ShareExpiryOption[]).map((option) => (
                    <option key={option} value={option}>
                      {SHARE_EXPIRY_LABELS[option]}
                    </option>
                  ))}
                </select>
              </div>

              {error && <p className="text-xs text-red-500">{error}</p>}

              <button
                type="button"
                onClick={handleGenerate}
                disabled={!workspace || isGenerating || isReadOnly}
                className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-sm font-medium text-white bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isGenerating ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Link2 size={14} />
                    Generate Share Link
                  </>
                )}
              </button>

              {shareUrl && (
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <input
                      readOnly
                      value={shareUrl}
                      aria-label="Generated share link"
                      className="flex-1 text-xs font-mono bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-200 truncate"
                    />
                    <button
                      type="button"
                      onClick={handleCopy}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-300"
                      title="Copy share link"
                      aria-label="Copy share link"
                    >
                      {copied ? (
                        <Check size={14} className="text-green-500" aria-hidden="true" />
                      ) : (
                        <Copy size={14} aria-hidden="true" />
                      )}
                      {copied ? "Copied!" : "Copy"}
                    </button>
                  </div>
                  {copyError && <p className="text-xs text-red-500">{copyError}</p>}
                  <p className="text-[11px] text-gray-400 dark:text-gray-500">
                    This link opens the saved version.
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
