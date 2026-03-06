import { useEffect } from "react";
import { Info, BookOpen, Hash, Lightbulb, FunctionSquare } from "lucide-react";
import { usePipelineStore } from "../store/pipelineStore";
import { operatorDocs } from "../data/operatorDocs";

export default function InfoPane() {
  const selectedBlockType = usePipelineStore((s) => s.selectedBlockType);
  const selectedBlockTooltip = usePipelineStore((s) => s.selectedBlockTooltip);

  // Dev-time check: warn about block types that have no documentation entry.
  // Uses a dynamic import so the categories module is excluded from the production bundle.
  useEffect(() => {
    if (import.meta.env.DEV) {
      import("../blocks/categories").then(({ categories }) => {
        const missingDocs = categories
          .flatMap((cat) => cat.blocks)
          .filter((block) => !operatorDocs[block.type])
          .map((block) => block.type);
        if (missingDocs.length > 0) {
          console.warn("[InfoPane] Missing documentation for block types:", missingDocs);
        }

        // Reverse check: doc keys that have no matching block type catch silent mismatches.
        const allBlockTypes = new Set(categories.flatMap((c) => c.blocks.map((b) => b.type)));
        Object.keys(operatorDocs).forEach((key) => {
          if (!allBlockTypes.has(key)) {
            console.warn(`[InfoPane] Doc key '${key}' has no matching block type.`);
          }
        });
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // stable module-level ref — empty deps is intentional

  if (!selectedBlockType) {
    return (
      <div className="flex flex-col items-center justify-center p-6 text-gray-400 text-xs text-center border-t border-gray-200">
        <Lightbulb size={20} className="mb-2" />
        <p>Select a block to view its documentation</p>
      </div>
    );
  }

  const doc = operatorDocs[selectedBlockType];

  // Fallback to simple tooltip view if no rich documentation exists
  if (!doc) {
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

  // Rich documentation view
  return (
    <div className="flex flex-col max-h-[40vh] overflow-y-auto bg-white border-t border-gray-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] text-sm">
      <div className="sticky top-0 bg-gray-50 px-4 py-2 border-b border-gray-200 flex items-center gap-2">
        <BookOpen size={16} className="text-indigo-500" />
        <h3 className="font-semibold text-gray-800">{doc.name}</h3>
        <span className="text-xs text-gray-400 font-mono ml-auto bg-gray-100 px-1.5 py-0.5 rounded">
          {selectedBlockType}
        </span>
      </div>

      <div className="p-4 space-y-4">
        {/* Description */}
        <div>
          <p className="text-gray-600 leading-relaxed">{doc.description}</p>
        </div>

        {/* Formula */}
        {doc.formula && (
          <div className="bg-gray-50 rounded-md p-3 border border-gray-100 flex items-start gap-3">
            <FunctionSquare size={16} className="text-gray-400 mt-0.5" />
            <code className="text-gray-800 font-mono text-xs">{doc.formula}</code>
          </div>
        )}

        <div className="flex flex-col gap-6">
          {/* Parameters */}
          {doc.parameters.length > 0 && (
            <div>
              <h4 className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                <Hash size={12} />
                Parameters
              </h4>
              <ul className="space-y-2">
                {doc.parameters.map((param, idx) => (
                  <li key={idx} className="text-xs flex flex-col gap-0.5">
                    <span className="font-semibold text-gray-700">{param.name}</span>
                    <span className="text-gray-500">{param.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Use Cases */}
          {doc.useCases.length > 0 && (
            <div>
              <h4 className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                <Lightbulb size={12} />
                Common Uses
              </h4>
              <ul className="list-disc leading-relaxed list-inside text-xs text-gray-600 space-y-1">
                {doc.useCases.map((useCase, idx) => (
                  <li key={idx}>{useCase}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
