import { Info } from 'lucide-react';
import { usePipelineStore } from '../store/pipelineStore';

export default function InfoPane() {
  const selectedBlockType = usePipelineStore((s) => s.selectedBlockType);
  const selectedBlockTooltip = usePipelineStore((s) => s.selectedBlockTooltip);

  if (!selectedBlockType) return null;

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 border-t border-gray-200 text-xs text-gray-600">
      <Info size={12} />
      <span className="font-medium">{selectedBlockType}</span>
      {selectedBlockTooltip && (
        <>
          <span className="text-gray-300">|</span>
          <span>{selectedBlockTooltip}</span>
        </>
      )}
    </div>
  );
}
