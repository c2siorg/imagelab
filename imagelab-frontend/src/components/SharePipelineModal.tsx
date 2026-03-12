import { useState, useEffect } from "react";
import * as Blockly from "blockly";
import { X, Copy, Check, Share2, Upload } from "lucide-react";

const READ_IMAGE_BLOCK_TYPE = "basic_readimage";
const FILENAME_LABEL_FIELD = "filename_label";

interface SharePipelineModalProps {
  workspace: Blockly.WorkspaceSvg | null;
  onClose: () => void;
}

function compressToCode(workspace: Blockly.WorkspaceSvg): string {
  const state = Blockly.serialization.workspaces.save(workspace);
  const json = JSON.stringify(state);
  const bytes = new TextEncoder().encode(json);
  let binary = "";
  bytes.forEach((b) => (binary += String.fromCharCode(b)));
  return btoa(binary);
}

function decompressFromCode(code: string): unknown {
  const binary = atob(code.trim());
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  const json = new TextDecoder().decode(bytes);
  return JSON.parse(json);
}

export default function SharePipelineModal({ workspace, onClose }: SharePipelineModalProps) {
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);
  const [inputCode, setInputCode] = useState("");
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadSuccess, setLoadSuccess] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const handleGenerate = () => {
    if (!workspace) return;
    const blocks = workspace.getAllBlocks(false);
    if (blocks.length === 0) {
      setGeneratedCode("");
      return;
    }
    const code = compressToCode(workspace);
    setGeneratedCode(code);
  };

  const handleCopy = async () => {
    if (!generatedCode) return;
    try {
      await navigator.clipboard.writeText(generatedCode);
      setCopied(true);
      setCopyError(null);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopyError("Could not copy to clipboard. Please select and copy manually.");
    }
  };

  const handleLoad = () => {
    if (!workspace || !inputCode.trim()) return;
    setLoadError(null);
    setLoadSuccess(false);

    const existingBlocks = workspace.getAllBlocks(false);
    if (existingBlocks.length > 0) {
      if (!window.confirm("Loading a pipeline will replace your current workspace. Continue?"))
        return;
    }

    try {
      const state = decompressFromCode(inputCode.trim());
      const snapshot = Blockly.serialization.workspaces.save(workspace);
      workspace.clear();

      try {
        Blockly.serialization.workspaces.load(
          state as Parameters<typeof Blockly.serialization.workspaces.load>[0],
          workspace,
        );
      } catch (loadErr) {
        Blockly.serialization.workspaces.load(snapshot, workspace);
        throw loadErr;
      }

      workspace.getBlocksByType(READ_IMAGE_BLOCK_TYPE, false).forEach((block) => {
        block.getField(FILENAME_LABEL_FIELD)?.setValue("No image");
      });

      setLoadSuccess(true);
      setTimeout(() => onClose(), 800);
    } catch {
      setLoadError("Invalid code. Please check and try again.");
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={onClose}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Share Pipeline"
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
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

        <div className="p-5 space-y-6">
          {/* Generate section */}
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wide">
                Generate Code
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Share your current pipeline with others using a code.
              </p>
            </div>

            <button
              type="button"
              onClick={handleGenerate}
              disabled={!workspace}
              className="w-full py-2 px-3 rounded-lg text-sm font-medium text-white bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Generate shareable pipeline code"
            >
              Generate Code
            </button>

            {generatedCode !== null && (
              <div className="space-y-2">
                {generatedCode === "" ? (
                  <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                    No blocks in workspace. Add some blocks first.
                  </p>
                ) : (
                  <>
                    <div className="flex gap-2">
                      <input
                        readOnly
                        value={generatedCode}
                        aria-label="Generated pipeline code"
                        placeholder="Generated code will appear here"
                        className="flex-1 text-xs font-mono bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-200 truncate"
                      />
                      <button
                        type="button"
                        onClick={handleCopy}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-300"
                        title="Copy code to clipboard"
                        aria-label="Copy code to clipboard"
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
                      Anyone with this code can load your pipeline.
                    </p>
                  </>
                )}
              </div>
            )}
          </div>

          <div className="border-t border-gray-100 dark:border-gray-700" />

          {/* Load section */}
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wide">
                Load from Code
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Paste a pipeline code to load it into your workspace.
              </p>
            </div>

            <textarea
              value={inputCode}
              onChange={(e) => {
                setInputCode(e.target.value);
                setLoadError(null);
                setLoadSuccess(false);
              }}
              aria-label="Paste pipeline code here"
              placeholder="Paste pipeline code here..."
              rows={3}
              className="w-full text-xs font-mono bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-200 dark:placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent"
            />

            {loadError && <p className="text-xs text-red-500">{loadError}</p>}
            {loadSuccess && (
              <p className="text-xs text-green-600 dark:text-green-400">
                Pipeline loaded successfully!
              </p>
            )}

            <button
              type="button"
              onClick={handleLoad}
              disabled={!inputCode.trim() || !workspace}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-sm font-medium text-white bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Load pipeline from code"
            >
              <Upload size={14} aria-hidden="true" />
              Load Pipeline
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
