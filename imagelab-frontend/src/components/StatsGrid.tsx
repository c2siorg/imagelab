import type { ImageAnalysis } from "../types/pipeline";

interface StatsGridProps {
  analysis: ImageAnalysis;
}

function formatNumber(value: number): string {
  if (!Number.isFinite(value)) return "n/a";
  if (Math.abs(value) >= 100) return value.toFixed(1);
  if (Number.isInteger(value)) return String(value);
  return value.toFixed(2);
}

function formatValue(value: number | number[]): string {
  if (Array.isArray(value)) {
    return value.map(formatNumber).join(" / ");
  }
  return formatNumber(value);
}

function gcd(a: number, b: number): number {
  while (b !== 0) {
    const next = a % b;
    a = b;
    b = next;
  }
  return a;
}

function aspectRatio(width: number, height: number): string {
  if (width <= 0 || height <= 0) return "n/a";
  const divisor = gcd(width, height);
  return `${width / divisor}:${height / divisor}`;
}

function StatItem({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="min-w-0 rounded border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 px-2 py-1">
      <div className="truncate text-[10px] uppercase font-semibold text-gray-400 dark:text-gray-500">
        {label}
      </div>
      <div
        className="truncate text-xs font-medium text-gray-800 dark:text-gray-100"
        title={String(value)}
      >
        {value}
      </div>
    </div>
  );
}

export default function StatsGrid({ analysis }: StatsGridProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
      <StatItem label="Resolution" value={`${analysis.width} x ${analysis.height}`} />
      <StatItem label="Aspect" value={aspectRatio(analysis.width, analysis.height)} />
      <StatItem label="Channels" value={analysis.channels} />
      <StatItem
        label="Range"
        value={`${formatNumber(analysis.min)} - ${formatNumber(analysis.max)}`}
      />
      <StatItem label="Mean" value={formatValue(analysis.mean)} />
      <StatItem label="Std dev" value={formatValue(analysis.std)} />
      <StatItem label="Data type" value={analysis.dtype} />
    </div>
  );
}
