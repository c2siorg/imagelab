import React, { useState, useEffect, useRef } from "react";
import {
  X,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Download,
  Trash2,
  Play,
  RotateCcw,
} from "lucide-react";
import { createBatchJob, getBatchJobStatus, getBatchJobDownloadUrl } from "../api/batch";
import type { PipelineGraph } from "../types/macro";
import type { BatchJobSummary } from "../types/batch";

interface BatchProcessingModalProps {
  graph: PipelineGraph;
  onClose: () => void;
}

const formatSize = (bytes: number) => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

export default function BatchProcessingModal({ graph, onClose }: BatchProcessingModalProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [imageFormat, setImageFormat] = useState<string>("png");
  const [isDragOver, setIsDragOver] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [summary, setSummary] = useState<BatchJobSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    dialogRef.current?.focus();
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isSubmitting && !isDownloading) {
        // Only allow close on Escape if not active in a blocker action
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose, isSubmitting, isDownloading]);

  // Polling logic when jobId is active
  useEffect(() => {
    if (!jobId) return;

    let timerId: ReturnType<typeof setTimeout>;

    const poll = async () => {
      try {
        const data = await getBatchJobStatus(jobId);
        setSummary(data);

        if (data.status === "completed" || data.status === "failed") {
          // Finished processing
          return;
        }

        // Keep polling
        timerId = setTimeout(poll, 1000);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to poll job status");
      }
    };

    poll();

    return () => {
      if (timerId) clearTimeout(timerId);
    };
  }, [jobId]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files).filter(
        (file) =>
          file.type.startsWith("image/") || file.name.match(/\.(png|jpe?g|webp|bmp|tiff)$/i),
      );
      setFiles((prev) => [...prev, ...droppedFiles]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearFiles = () => {
    setFiles([]);
  };

  const handleStartBatch = async () => {
    if (files.length === 0) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await createBatchJob(files, graph, imageFormat);
      setJobId(response.job_id);
      // Initialize layout summary state
      setSummary({
        job_id: response.job_id,
        status: "pending",
        total_files: files.length,
        processed_files: 0,
        success_count: 0,
        failure_count: 0,
        created_at: Date.now() / 1000,
        updated_at: Date.now() / 1000,
        duration_seconds: 0,
        results: [],
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start batch processing");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownloadZip = async () => {
    if (!jobId) return;
    setIsDownloading(true);
    try {
      const url = getBatchJobDownloadUrl(jobId);
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to download: status ${response.status}`);
      }
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = `batch_results_${jobId.substring(0, 8)}.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to download batch results ZIP");
    } finally {
      setIsDownloading(false);
    }
  };

  const handleReset = () => {
    setFiles([]);
    setJobId(null);
    setSummary(null);
    setError(null);
  };

  const isFinished = summary?.status === "completed" || summary?.status === "failed";
  const progressPercent = summary
    ? Math.round((summary.processed_files / summary.total_files) * 100)
    : 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      role="none"
      onClick={() => {
        if (!isSubmitting && !isDownloading && !jobId) {
          onClose();
        }
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="batch-modal-title"
        tabIndex={-1}
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden outline-none border border-gray-100 dark:border-gray-700 flex flex-col max-h-[90vh] transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex flex-col">
            <h2
              id="batch-modal-title"
              className="text-lg font-bold text-gray-800 dark:text-gray-150"
            >
              Batch Image Processing
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Run active Blockly pipeline steps on multiple files concurrently
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting || (jobId !== null && !isFinished)}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-450 dark:text-gray-400 hover:text-gray-650 dark:hover:text-gray-200 transition-colors disabled:opacity-40"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 flex-1 overflow-y-auto space-y-6">
          {error && (
            <div className="flex items-start gap-3 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-xl text-red-750 dark:text-red-300 text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <span className="font-semibold">Error:</span> {error}
              </div>
            </div>
          )}

          {/* Setup / Upload Mode */}
          {!jobId && (
            <>
              {/* Drag and Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`relative h-44 rounded-xl border-2 border-dashed flex flex-col items-center justify-center p-6 text-center cursor-pointer transition-all duration-200 ${
                  isDragOver
                    ? "border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20"
                    : "border-gray-300 dark:border-gray-700 hover:border-indigo-400 hover:bg-gray-50/50 dark:hover:bg-gray-850/35"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <UploadCloud className="w-12 h-12 text-gray-450 dark:text-gray-500 mb-3 animate-pulse" />
                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Drag & drop your images here, or click to browse
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Supports PNG, JPEG, WebP, etc.
                </span>
              </div>

              {/* Selected Files List */}
              {files.length > 0 && (
                <div className="space-y-2">
                  <div className="flex justify-between items-center px-1">
                    <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                      Selected Files ({files.length})
                    </span>
                    <button
                      type="button"
                      onClick={clearFiles}
                      className="text-xs text-red-500 hover:text-red-650 flex items-center gap-1 font-medium transition-colors"
                    >
                      <Trash2 size={12} />
                      Remove All
                    </button>
                  </div>
                  <div className="border border-gray-150 dark:border-gray-700 rounded-xl divide-y divide-gray-150 dark:divide-gray-700 max-h-48 overflow-y-auto">
                    {files.map((file, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3 bg-gray-50/50 dark:bg-gray-800/30 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-850"
                      >
                        <div className="flex flex-col min-w-0 pr-4">
                          <span className="font-medium truncate max-w-sm">{file.name}</span>
                          <span className="text-xxs text-gray-450 dark:text-gray-500">
                            {formatSize(file.size)}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeFile(idx)}
                          className="p-1 rounded-md text-gray-400 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-950/30 dark:hover:text-red-400 transition-colors"
                          title="Remove file"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Format & Execution Controls */}
              <div className="flex items-center gap-4 bg-gray-50 dark:bg-gray-850/50 p-4 rounded-xl border border-gray-150 dark:border-gray-750">
                <div className="flex flex-col gap-1 w-1/3">
                  <label
                    htmlFor="format-select"
                    className="text-xs font-semibold text-gray-500 dark:text-gray-450"
                  >
                    Output Image Format
                  </label>
                  <select
                    id="format-select"
                    value={imageFormat}
                    onChange={(e) => setImageFormat(e.target.value)}
                    className="w-full text-sm rounded-lg border border-gray-350 dark:border-gray-650 bg-white dark:bg-gray-800 px-3 py-1.5 text-gray-800 dark:text-gray-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="png">PNG (Default)</option>
                    <option value="jpeg">JPEG</option>
                    <option value="webp">WebP</option>
                  </select>
                </div>

                <div className="flex-1 flex justify-end items-end h-full mt-auto">
                  <button
                    type="button"
                    onClick={handleStartBatch}
                    disabled={files.length === 0 || isSubmitting}
                    className="w-full flex items-center justify-center gap-2 px-5 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold shadow-md shadow-indigo-500/10 hover:shadow-indigo-500/25 transition-all"
                  >
                    {isSubmitting ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Play size={16} />
                    )}
                    {isSubmitting ? "Starting Batch..." : `Process ${files.length} Images`}
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Running / Results View */}
          {jobId && summary && (
            <div className="space-y-6">
              {/* Progress and status */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    {!isFinished ? (
                      <Loader2 size={16} className="text-indigo-500 animate-spin" />
                    ) : summary.failure_count > 0 ? (
                      <AlertCircle size={16} className="text-amber-500" />
                    ) : (
                      <CheckCircle2 size={16} className="text-emerald-500" />
                    )}
                    <span className="text-sm font-bold text-gray-800 dark:text-gray-200">
                      {!isFinished
                        ? "Processing Images..."
                        : summary.failure_count > 0
                          ? "Batch Run Completed with Failures"
                          : "Batch Run Completed Successfully"}
                    </span>
                  </div>
                  <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 font-mono">
                    {summary.processed_files} / {summary.total_files}
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    style={{ width: `${progressPercent}%` }}
                    className={`h-full rounded-full transition-all duration-300 ${
                      !isFinished
                        ? "bg-gradient-to-r from-indigo-500 to-purple-500 animate-pulse"
                        : summary.failure_count > 0
                          ? "bg-amber-500"
                          : "bg-emerald-500"
                    }`}
                  />
                </div>
              </div>

              {/* Statistics Grid */}
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-gray-55/60 dark:bg-gray-850/40 p-3 rounded-xl border border-gray-150 dark:border-gray-750 flex flex-col items-center">
                  <span className="text-[10px] uppercase font-semibold text-gray-500 dark:text-gray-450 tracking-wider">
                    Total
                  </span>
                  <span className="text-xl font-bold text-gray-800 dark:text-gray-200 mt-1">
                    {summary.total_files}
                  </span>
                </div>
                <div className="bg-emerald-50/20 dark:bg-emerald-950/10 p-3 rounded-xl border border-emerald-100 dark:border-emerald-900/35 flex flex-col items-center">
                  <span className="text-[10px] uppercase font-semibold text-emerald-600 dark:text-emerald-450 tracking-wider">
                    Success
                  </span>
                  <span className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                    {summary.success_count}
                  </span>
                </div>
                <div className="bg-red-50/20 dark:bg-red-950/10 p-3 rounded-xl border border-red-100 dark:border-red-900/35 flex flex-col items-center">
                  <span className="text-[10px] uppercase font-semibold text-red-500 dark:text-red-450 tracking-wider">
                    Failed
                  </span>
                  <span className="text-xl font-bold text-red-500 dark:text-red-400 mt-1">
                    {summary.failure_count}
                  </span>
                </div>
                <div className="bg-gray-55/60 dark:bg-gray-850/40 p-3 rounded-xl border border-gray-150 dark:border-gray-750 flex flex-col items-center">
                  <span className="text-[10px] uppercase font-semibold text-gray-500 dark:text-gray-455 tracking-wider">
                    Duration
                  </span>
                  <span className="text-xl font-bold text-gray-800 dark:text-gray-200 mt-1 font-mono">
                    {summary.duration_seconds.toFixed(1)}s
                  </span>
                </div>
              </div>

              {/* Results List */}
              {summary.results && summary.results.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 px-1">
                    Processing Details
                  </span>
                  <div className="border border-gray-150 dark:border-gray-700 rounded-xl divide-y divide-gray-150 dark:divide-gray-700 max-h-52 overflow-y-auto">
                    {summary.results.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex flex-col p-3 bg-gray-50/30 dark:bg-gray-800/20 text-sm text-gray-750 dark:text-gray-300"
                      >
                        <div className="flex items-center justify-between w-full">
                          <span className="font-medium truncate max-w-md">{item.filename}</span>
                          <div className="flex items-center gap-1.5">
                            {item.success ? (
                              <>
                                <CheckCircle2 size={14} className="text-emerald-500" />
                                <span className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold">
                                  Success
                                </span>
                              </>
                            ) : (
                              <>
                                <AlertCircle size={14} className="text-red-500" />
                                <span className="text-xs text-red-500 dark:text-red-400 font-semibold">
                                  Failed
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                        {item.success && item.output_filename && (
                          <span className="text-xxs text-gray-450 dark:text-gray-500 mt-0.5">
                            Output: {item.output_filename}
                          </span>
                        )}
                        {!item.success && item.error && (
                          <div className="text-xxs text-red-500/90 dark:text-red-400/90 bg-red-50/50 dark:bg-red-950/20 border border-red-100/70 dark:border-red-900/30 p-2 rounded-md mt-1.5 font-mono break-all whitespace-pre-wrap">
                            {item.error}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer controls for results state */}
        {jobId && (
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-800/40">
            <button
              type="button"
              onClick={handleReset}
              disabled={isDownloading || !isFinished}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-xs font-semibold text-gray-650 dark:text-gray-350 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-40"
            >
              <RotateCcw size={14} />
              New Batch
            </button>

            <button
              type="button"
              onClick={handleDownloadZip}
              disabled={!isFinished || isDownloading}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold shadow-md shadow-emerald-500/10 hover:shadow-emerald-500/25 transition-all"
            >
              {isDownloading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Download size={16} />
              )}
              {isDownloading ? "Downloading ZIP..." : "Download ZIP"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
