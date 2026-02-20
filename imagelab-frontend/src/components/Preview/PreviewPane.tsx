import { useState } from "react";
import { ZoomIn, ZoomOut } from "lucide-react";
import { usePipelineStore } from "../../store/pipelineStore";
import ImageDisplay from "./ImageDisplay";

export default function PreviewPane() {
  const { originalImage, imageFormat, processedImage, error } = usePipelineStore();

  const [zoomWidth, setZoomWidth] = useState<number | null>(null);

  const handleZoomIn = () => {
    setZoomWidth((prev) => Math.min((prev ?? 300) + 100, 2500));
  };
  const handleZoomOut = () => {
    setZoomWidth((prev) => Math.max((prev ?? 300) - 100, 100));
  };

  const displayImage = processedImage || originalImage;

  return (
    <div className="w-80 h-full bg-white border-l border-gray-200 flex flex-col flex-shrink-0">
      <div className="px-3 py-2 border-b border-gray-200">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Preview</h2>
      </div>

      <div className="flex-1 flex items-center justify-center p-3 bg-gray-50 overflow-auto">
        {displayImage ? (
          <ImageDisplay image={displayImage} format={imageFormat} zoomWidth={zoomWidth} />
        ) : (
          <p className="text-sm text-gray-400">Use the Read Image block to upload</p>
        )}
      </div>

      {error && (
        <div className="px-3 py-2 bg-red-50 border-t border-red-200">
          <p className="text-xs text-red-600">{error}</p>
        </div>
      )}

      <div className="p-3 border-t border-gray-200 flex justify-center gap-2">
        <button
          onClick={handleZoomIn}
          disabled={!displayImage}
          className="flex items-center justify-center gap-1.5 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Zoom In"
        >
          <ZoomIn size={16} />
        </button>
        <button
          onClick={handleZoomOut}
          disabled={!displayImage}
          className="flex items-center justify-center gap-1.5 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Zoom Out"
        >
          <ZoomOut size={16} />
        </button>
      </div>
    </div>
  );
}
