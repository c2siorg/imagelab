import { useEffect, useRef } from "react";

interface HistogramCanvasProps {
  histograms: number[][];
  height?: number;
}

const CHANNEL_COLORS = ["#3b82f6", "#22c55e", "#ef4444"]; // B, G, R
const GRAY_COLOR = "#6b7280";

export default function HistogramCanvas({ histograms, height = 64 }: HistogramCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const dpr = window.devicePixelRatio || 1;
    const cssWidth = canvas.offsetWidth || 200;
    canvas.width = cssWidth * dpr;
    canvas.height = height * dpr;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, cssWidth, height);

    const globalMax = Math.max(...histograms.flatMap((h) => h));
    if (globalMax === 0) return;

    const binWidth = cssWidth / 256;
    const isGray = histograms.length === 1;

    histograms.forEach((hist, ci) => {
      ctx.beginPath();
      ctx.strokeStyle = isGray ? GRAY_COLOR : (CHANNEL_COLORS[ci] ?? GRAY_COLOR);
      ctx.lineWidth = 1;
      ctx.globalAlpha = isGray ? 0.9 : 0.7;

      hist.forEach((count, bin) => {
        const x = bin * binWidth;
        const barH = (count / globalMax) * height;
        const y = height - barH;
        if (bin === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });

      ctx.stroke();
    });

    ctx.globalAlpha = 1;
  }, [histograms, height]);

  return (
    <canvas ref={canvasRef} className="w-full" style={{ height }} aria-label="Pixel histogram" />
  );
}
