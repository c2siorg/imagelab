import { useEffect, useMemo, useRef, useState } from "react";

interface HistogramCanvasProps {
  image: string | null;
  format: string;
  channels: number;
}

interface HistogramData {
  red: number[];
  green: number[];
  blue: number[];
  luminance: number[];
}

type Channel = "luminance" | "red" | "green" | "blue";

interface HistogramState {
  imageKey: string | null;
  histogram: HistogramData | null;
  error: string | null;
}

const CHANNEL_META: Record<Channel, { label: string; stroke: string }> = {
  luminance: { label: "Luma", stroke: "#6B7280" },
  red: { label: "Red", stroke: "#EF4444" },
  green: { label: "Green", stroke: "#22C55E" },
  blue: { label: "Blue", stroke: "#3B82F6" },
};

function emptyHistogram(): HistogramData {
  return {
    red: Array(256).fill(0),
    green: Array(256).fill(0),
    blue: Array(256).fill(0),
    luminance: Array(256).fill(0),
  };
}

async function calculateHistogram(image: string, format: string): Promise<HistogramData> {
  const img = new Image();
  img.decoding = "async";
  img.src = `data:image/${format};base64,${image}`;

  await new Promise<void>((resolve, reject) => {
    img.onload = () => resolve();
    img.onerror = () => reject(new Error("Could not decode image for histogram"));
  });

  const canvas = document.createElement("canvas");
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) throw new Error("Canvas is unavailable");

  ctx.drawImage(img, 0, 0);
  const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  const histogram = emptyHistogram();

  for (let i = 0; i < pixels.length; i += 4) {
    const red = pixels[i];
    const green = pixels[i + 1];
    const blue = pixels[i + 2];
    const luminance = Math.round(0.2126 * red + 0.7152 * green + 0.0722 * blue);

    histogram.red[red] += 1;
    histogram.green[green] += 1;
    histogram.blue[blue] += 1;
    histogram.luminance[luminance] += 1;
  }

  return histogram;
}

export default function HistogramCanvas({ image, format, channels }: HistogramCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [histogramState, setHistogramState] = useState<HistogramState>({
    imageKey: null,
    histogram: null,
    error: null,
  });
  const [visibleChannels, setVisibleChannels] = useState<Record<Channel, boolean>>({
    luminance: true,
    red: false,
    green: false,
    blue: false,
  });

  const hasColor = channels > 1;
  const imageKey = image ? `${format}:${image}` : null;
  const histogram = histogramState.imageKey === imageKey ? histogramState.histogram : null;
  const error = histogramState.imageKey === imageKey ? histogramState.error : null;
  const effectiveVisibleChannels = useMemo(
    () => ({
      luminance: visibleChannels.luminance || !hasColor,
      red: hasColor && visibleChannels.red,
      green: hasColor && visibleChannels.green,
      blue: hasColor && visibleChannels.blue,
    }),
    [hasColor, visibleChannels],
  );

  useEffect(() => {
    let isCancelled = false;

    if (!image || !imageKey) return;

    calculateHistogram(image, format)
      .then((nextHistogram) => {
        if (!isCancelled) {
          setHistogramState({ imageKey, histogram: nextHistogram, error: null });
        }
      })
      .catch((err) => {
        if (!isCancelled) {
          setHistogramState({
            imageKey,
            histogram: null,
            error: err instanceof Error ? err.message : "Could not draw histogram",
          });
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [format, image, imageKey]);

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

    const maxFrequency = Math.max(1, ...drawableChannels.flatMap((channel) => histogram[channel]));
    const xStep = width / 255;

    drawableChannels.forEach((channel) => {
      const values = histogram[channel];
      ctx.strokeStyle = CHANNEL_META[channel].stroke;
      ctx.lineWidth = channel === "luminance" ? 1.75 : 1.35;
      ctx.beginPath();

      values.forEach((count, index) => {
        const x = index * xStep;
        const normalized = count / maxFrequency;
        const y = height - normalized * (height - 8) - 4;
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });

      ctx.stroke();
    });
  }, [drawableChannels, histogram]);

  const toggleChannel = (channel: Channel) => {
    setVisibleChannels((current) => ({ ...current, [channel]: !current[channel] }));
  };

  return (
    <div className="h-full min-h-[112px] flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        {(Object.keys(CHANNEL_META) as Channel[]).map((channel) => {
          const disabled = channel !== "luminance" && !hasColor;
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
                {CHANNEL_META[channel].label}
              </span>
            </label>
          );
        })}
      </div>
      <div className="relative min-h-0 flex-1 rounded border border-gray-200 dark:border-gray-700 overflow-hidden">
        <canvas ref={canvasRef} className="h-full w-full block bg-gray-50 dark:bg-gray-900" />
        {!histogram && !error && image && (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-400 dark:text-gray-500">
            Loading histogram
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center px-3 text-center text-xs text-red-500 dark:text-red-400">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
