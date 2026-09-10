import { useEffect, useMemo, useState } from "react";
import { Loader2, Pencil, X } from "lucide-react";
import { useMacroStore } from "../../store/useMacroStore";
import type { ExposedParam, MacroDefinition } from "../../types/macro";
import { formatExposedFieldKey } from "../../utils/macroFieldKeys";
import { findDependentMacros } from "../../utils/macroDependencies";
import { cleanNestedMacroParamLabel } from "../../utils/extractMacroGraph";

interface EditMacroModalProps {
  macro: MacroDefinition;
  onClose: () => void;
}

interface EditableParam extends ExposedParam {
  enabled: boolean;
}

function candidatesFor(macro: MacroDefinition): EditableParam[] {
  const existing = new Map(
    (macro.exposedParams ?? macro.graph.exposed_params ?? []).map((param) => [
      formatExposedFieldKey(param.blockId, param.paramName),
      param,
    ]),
  );
  const candidates: EditableParam[] = [];
  for (const node of macro.graph.nodes) {
    for (const [paramName, defaultValue] of Object.entries(node.params ?? {})) {
      const key = formatExposedFieldKey(node.id, paramName);
      const saved = existing.get(key);
      candidates.push({
        blockId: node.id,
        blockType: node.type ?? node.op ?? "unknown",
        paramName,
        label:
          saved?.label ??
          `${cleanNestedMacroParamLabel(paramName)} (${node.type ?? node.op ?? "unknown"})`,
        defaultValue: saved?.defaultValue ?? defaultValue,
        enabled: saved !== undefined,
      });
    }
  }
  return candidates;
}

function inputValue(value: unknown): string {
  return typeof value === "string" || typeof value === "number" ? String(value) : "";
}

export default function EditMacroModal({ macro, onClose }: EditMacroModalProps) {
  const updateMacro = useMacroStore((state) => state.updateMacro);
  const [params, setParams] = useState<EditableParam[]>(() => candidatesFor(macro));
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const originalExposed = useMemo(
    () => macro.exposedParams ?? macro.graph.exposed_params ?? [],
    [macro],
  );

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const updateParam = (index: number, updates: Partial<EditableParam>) => {
    setParams((previous) =>
      previous.map((param, i) => (i === index ? { ...param, ...updates } : param)),
    );
  };

  const handleSubmit: React.ComponentProps<"form">["onSubmit"] = async (event) => {
    event.preventDefault();
    const exposedParams = params
      .filter((param) => param.enabled)
      .map(
        (param): ExposedParam => ({
          blockId: param.blockId,
          blockType: param.blockType,
          paramName: param.paramName,
          label: param.label,
          defaultValue: param.defaultValue,
        }),
      );
    const exposedKeys = new Set(
      exposedParams.map((param) => formatExposedFieldKey(param.blockId, param.paramName)),
    );
    const removed = originalExposed.filter(
      (param) => !exposedKeys.has(formatExposedFieldKey(param.blockId, param.paramName)),
    );
    const dependents = findDependentMacros(
      macro.id,
      removed.map((param) => formatExposedFieldKey(param.blockId, param.paramName)),
    );
    if (dependents.length > 0 && removed.length > 0) {
      setError(
        `Cannot remove parameter '${cleanNestedMacroParamLabel(removed[0].paramName)}' because it is exposed/used in dependent macro '${dependents[0].name}'.`,
      );
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      await updateMacro(macro.id, {
        pipeline_json: {
          nodes: macro.graph.nodes,
          edges: macro.graph.edges,
          exposed_params: exposedParams,
        },
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update macro");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 backdrop-blur-xs"
      onClick={onClose}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Edit Macro"
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden border border-gray-200 dark:border-gray-700"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <div className="flex items-center gap-2">
            <Pencil size={18} className="text-indigo-500" />
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
              Edit {macro.name}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400"
          >
            <X size={16} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4 max-h-[80vh] overflow-y-auto">
          {error && (
            <div
              data-testid="error-banner"
              className="p-3 text-xs bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 rounded-lg"
            >
              {error}
            </div>
          )}
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Choose fields to expose and customize their labels and defaults.
          </p>
          <div className="space-y-2">
            {params.map((param, index) => (
              <div
                key={formatExposedFieldKey(param.blockId, param.paramName)}
                className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-2 p-3 rounded border border-gray-200 dark:border-gray-700"
              >
                <input
                  aria-label={`Expose ${param.paramName}`}
                  type="checkbox"
                  checked={param.enabled}
                  disabled={isSubmitting}
                  onChange={() => updateParam(index, { enabled: !param.enabled })}
                  className="mt-1 rounded border-gray-300 text-indigo-600"
                />
                <div className="space-y-2 min-w-0">
                  <div className="text-xs text-gray-400 font-mono truncate">
                    {cleanNestedMacroParamLabel(param.paramName)} · {param.blockType}
                  </div>
                  <input
                    aria-label={`Label for ${param.paramName}`}
                    value={param.label ?? ""}
                    disabled={isSubmitting || !param.enabled}
                    onChange={(event) => updateParam(index, { label: event.target.value })}
                    className="w-full text-xs rounded border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-2 py-1.5 dark:text-gray-100"
                  />
                  {typeof param.defaultValue === "boolean" ? (
                    <label className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                      <input
                        aria-label={`Default for ${param.paramName}`}
                        type="checkbox"
                        checked={param.defaultValue}
                        disabled={isSubmitting || !param.enabled}
                        onChange={(event) =>
                          updateParam(index, { defaultValue: event.target.checked })
                        }
                      />{" "}
                      Default value
                    </label>
                  ) : (
                    <input
                      aria-label={`Default for ${param.paramName}`}
                      type={typeof param.defaultValue === "number" ? "number" : "text"}
                      value={inputValue(param.defaultValue)}
                      disabled={isSubmitting || !param.enabled}
                      onChange={(event) =>
                        updateParam(index, {
                          defaultValue:
                            typeof param.defaultValue === "number"
                              ? Number(event.target.value)
                              : event.target.value,
                        })
                      }
                      className="w-full text-xs rounded border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-2 py-1.5 dark:text-gray-100"
                    />
                  )}
                </div>
              </div>
            ))}
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 py-2 px-3 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-600"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium text-white bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
