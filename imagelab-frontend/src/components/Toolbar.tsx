import * as Blockly from "blockly";
import { FilePlus, Download, Undo2, Redo2, Play, Loader2 } from "lucide-react";
import { usePipelineStore } from "../store/pipelineStore";
import { executePipeline } from "../api/pipeline";
import { extractPipeline } from "../hooks/usePipeline";

interface ToolbarProps {
  workspace: Blockly.WorkspaceSvg | null;
}

export default function Toolbar({ workspace }: ToolbarProps) {
  const {
    originalImage,
    imageFormat,
    processedImage,
    isExecuting,
    setProcessedImage,
    setExecuting,
    setError,
    reset,
  } = usePipelineStore();

  const handleNew = () => {
    if (
      !window.confirm("This will clear all blocks and the uploaded image. Continue?")
    ) {
      return;
    }
    reset();
    if (workspace) workspace.clear();
  };

  const handleDownload = () => {
    if (!processedImage) return;
    const link = document.createElement("a");
    link.href = `data:image/${imageFormat};base64,${processedImage}`;
    link.download = `processed.${imageFormat}`;
    link.click();
  };

  const handleUndo = () => workspace?.undo(false);
  const handleRedo = () => workspace?.undo(true);

  const handleRun = async () => {
    if (!workspace || !originalImage) return;

    const pipeline = extractPipeline(workspace);
    if (pipeline.length === 0) {
      setError('No pipeline found. Add a "Read Image" block and connect operations.');
      return;
    }

    setExecuting(true);
    setError(null);

    try {
      const response = await executePipeline({
        image: originalImage,
        image_format: imageFormat,
        pipeline,
      });

      if (response.success && response.image) {
        setProcessedImage(response.image);
      } else {
        setError(response.error || "Pipeline execution failed", response.step);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Network error");
    } finally {
      setExecuting(false);
    }
  };

  const iconBtn =
    "p-1.5 rounded hover:bg-gray-100 text-gray-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors";
  const separator = "w-px h-5 bg-gray-300 mx-1";

  return (
    <div className="h-10 flex items-center gap-1 px-3 bg-white border-b border-gray-200 flex-shrink-0">
      <button onClick={handleNew} className={iconBtn} title="New">
        <FilePlus size={18} />
      </button>
      <button
        onClick={handleDownload}
        disabled={!processedImage}
        className={iconBtn}
        title="Download"
      >
        <Download size={18} />
      </button>

      <div className={separator} />

      <button onClick={handleUndo} className={iconBtn} title="Undo">
        <Undo2 size={18} />
      </button>
      <button onClick={handleRedo} className={iconBtn} title="Redo">
        <Redo2 size={18} />
      </button>

      <div className={separator} />

      <button
        onClick={handleRun}
        disabled={isExecuting || !originalImage}
        className="flex items-center gap-1.5 px-3 py-1 rounded-md text-sm font-medium text-white bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title="Run Pipeline"
      >
        {isExecuting ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
        {isExecuting ? "Running..." : "Run"}
      </button>
    </div>
  );
}
