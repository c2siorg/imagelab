import { useEffect, useMemo, useRef, useState } from "react";
import type { ImageHistogram } from "../types/pipeline";

interface HistogramCanvasProps {
  histogram: ImageHistogram | null;
  channels: number;
}

type Channel = "luminance" | "red" | "green" | "blue";

const CHANNEL_META: Record<Channel, { label: string; stroke: string }> = {
  luminance: { label: "Luma", stroke: "#6B7280" },
  red: { label: "Red", stroke: "#EF4444" },
  green: { label: "Green", stroke: "#22C55E" },
  blue: { label: "Blue", stroke: "#3B82F6" },
};

function getChannelValues(histogram: ImageHistogram, channel: Channel): number[] | null {
  return histogram[channel] ?? null;
}

export default function HistogramCanvas({ histogram, channels }: HistogramCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [visibleChannels, setVisibleChannels] = useState<Record<Channel, boolean>>({
    luminance: true,
    red: false,
    green: false,
    blue: false,
  });
  const [scaleMode, setScaleMode] = useState<"log" | "linear">("log");

  const hasColor = channels > 1;
  const effectiveVisibleChannels = useMemo(
    () => ({
      luminance: visibleChannels.luminance || !hasColor,
      red: hasColor && visibleChannels.red && Boolean(histogram?.red),
      green: hasColor && visibleChannels.green && Boolean(histogram?.green),
      blue: hasColor && visibleChannels.blue && Boolean(histogram?.blue),
    }),
    [hasColor, histogram, visibleChannels],
  );

  const drawableChannels = useMemo(
    () =>
      (Object.keys(effectiveVisibleChannels) as Channel[]).filter(
        (channel) => effectiveVisibleChannels[channel],
      ),
    [effectiveVisibleChannels],
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const width = Math.max(1, canvas.clientWidth);
    const height = Math.max(1, canvas.clientHeight);
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.floor(width * ratio);
    canvas.height = Math.floor(height * ratio);

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.scale(ratio, ratio);
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#F9FAFB";
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = "#E5E7EB";
    ctx.lineWidth = 1;
    for (let i = 1; i < 4; i += 1) {
      const y = (height / 4) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    if (!histogram || drawableChannels.length === 0) return;

    const scaleFn = scaleMode === "log" ? Math.log1p : (x: number) => x;

    const visibleValues = drawableChannels.flatMap((channel) =>
      (getChannelValues(histogram, channel) ?? []).map((count) => scaleFn(count)),
    );
    const maxFrequency = Math.max(1, ...visibleValues);
    const xStep = width / Math.max(1, histogram.bins.length - 1);

    drawableChannels.forEach((channel) => {
      const values = getChannelValues(histogram, channel);
      if (!values) return;

      ctx.strokeStyle = CHANNEL_META[channel].stroke;
      ctx.lineWidth = channel === "luminance" ? 1.75 : 1.35;
      ctx.beginPath();

      values.forEach((count, index) => {
        const x = index * xStep;
        const normalized = scaleFn(count) / maxFrequency;
        const y = height - normalized * (height - 8) - 4;
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });

      ctx.stroke();
    });
  }, [drawableChannels, histogram, scaleMode]);

  const toggleChannel = (channel: Channel) => {
    setVisibleChannels((current) => ({ ...current, [channel]: !current[channel] }));
  };

  return (
    <div className="h-full min-h-[112px] flex flex-col gap-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          {(Object.keys(CHANNEL_META) as Channel[]).map((channel) => {
            const disabled = channel !== "luminance" && (!hasColor || !histogram?.[channel]);
            return (
              <label
                key={channel}
                className={`inline-flex items-center gap-1.5 text-[11px] font-medium ${
                  disabled ? "text-gray-300 dark:text-gray-600" : "text-gray-600 dark:text-gray-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={effectiveVisibleChannels[channel] && !disabled}
                  disabled={disabled}
                  onChange={() => toggleChannel(channel)}
                  className="h-3 w-3 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="inline-flex items-center gap-1">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: CHANNEL_META[channel].stroke }}
                  />
                  {channel === "luminance" && !hasColor ? "Intensity" : CHANNEL_META[channel].label}
                </span>
              </label>
            );
          })}
        </div>
        <div className="flex items-center gap-0.5 text-[10px] font-semibold text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700/50 p-0.5 rounded">
          <button
            type="button"
            onClick={() => setScaleMode("log")}
            className={`px-1.5 py-0.5 rounded-sm transition-all duration-150 ${
              scaleMode === "log"
                ? "bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-xs"
                : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            }`}
          >
            Log
          </button>
          <button
            type="button"
            onClick={() => setScaleMode("linear")}
            className={`px-1.5 py-0.5 rounded-sm transition-all duration-150 ${
              scaleMode === "linear"
                ? "bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-xs"
                : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            }`}
          >
            Linear
          </button>
        </div>
      </div>
      <div className="relative min-h-0 flex-1 rounded border border-gray-200 dark:border-gray-700 overflow-hidden">
        <canvas ref={canvasRef} className="h-full w-full block bg-gray-50 dark:bg-gray-900" />
        {!histogram && (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-400 dark:text-gray-500">
            Loading histogram
          </div>
        )}
      </div>
    </div>
  );
}
