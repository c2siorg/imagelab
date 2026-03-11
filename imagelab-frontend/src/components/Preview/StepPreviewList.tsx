import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { StepResult } from "../../types/pipeline";
import HistogramCanvas from "./HistogramCanvas";

interface StepPreviewListProps {
  steps: StepResult[];
}

function formatOperatorName(type: string): string {
  // e.g. "blurring_applyblur" -> "Apply Blur"
  const parts = type.split("_");
  const name = parts.slice(1).join(" ");
  return name.charAt(0).toUpperCase() + name.slice(1).replace(/([a-z])([A-Z])/g, "$1 $2");
}

function StatRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between text-[10px] text-gray-500 py-0.5">
      <span className="text-gray-400">{label}</span>
      <span className="font-mono text-gray-600">{value}</span>
    </div>
  );
}

function StepCard({ result, index }: { result: StepResult; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const { stats } = result;

  return (
    <div className="border border-gray-100 rounded-lg overflow-hidden bg-white shadow-sm">
      <button
        type="button"
        className="w-full flex items-center gap-2 p-2 hover:bg-gray-50 transition-colors text-left"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-indigo-100 text-indigo-600 text-[10px] font-bold flex items-center justify-center">
          {index + 1}
        </span>
        <img
          src={`data:image/jpeg;base64,${result.thumbnail}`}
          alt={`Step ${index + 1} output`}
          className="h-10 w-14 object-cover rounded border border-gray-100 flex-shrink-0"
        />
        <span className="flex-1 text-xs font-medium text-gray-700 truncate">
          {formatOperatorName(result.operator_type)}
        </span>
        <span className="flex-shrink-0 text-gray-400">
          {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        </span>
      </button>

      {expanded && (
        <div className="px-3 pb-3 border-t border-gray-50 bg-gray-50/50">
          <div className="mt-2 space-y-0.5">
            <StatRow label="Size" value={`${stats.width} × ${stats.height}`} />
            <StatRow label="Channels" value={stats.channels} />
            <StatRow label="Dtype" value={stats.dtype} />
            <StatRow label="Min" value={stats.min_val.toFixed(2)} />
            <StatRow label="Max" value={stats.max_val.toFixed(2)} />
            <StatRow label="Mean" value={stats.mean_val.toFixed(2)} />
          </div>
          <div className="mt-2 bg-gray-900 rounded p-1">
            <HistogramCanvas histograms={stats.histograms} height={56} />
          </div>
          <p className="text-[9px] text-gray-400 mt-1 text-center">
            {stats.channels === 1 ? "Grayscale" : "B · G · R"} histogram
          </p>
        </div>
      )}
    </div>
  );
}

export default function StepPreviewList({ steps }: StepPreviewListProps) {
  if (steps.length === 0) {
    return (
      <div className="flex items-center justify-center h-24 text-xs text-gray-400">
        No steps to display
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 p-2 overflow-y-auto">
      {steps.map((result, i) => (
        <StepCard key={result.step} result={result} index={i} />
      ))}
    </div>
  );
}
