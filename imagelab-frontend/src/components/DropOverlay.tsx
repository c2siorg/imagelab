import { ImagePlus } from "lucide-react";

interface DropOverlayProps {
  visible: boolean;
}

export default function DropOverlay({ visible }: DropOverlayProps) {
  if (!visible) return null;

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-indigo-500/10 dark:bg-indigo-500/20 backdrop-blur-sm pointer-events-none">
      <div className="flex flex-col items-center gap-4 px-8 py-6 bg-white dark:bg-gray-800 rounded-2xl border-2 border-dashed border-indigo-500 dark:border-indigo-400 shadow-2xl">
        <ImagePlus className="w-16 h-16 text-indigo-500 dark:text-indigo-400 animate-bounce" />
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">Drop image here</p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Release to load into pipeline
          </p>
        </div>
      </div>
    </div>
  );
}
