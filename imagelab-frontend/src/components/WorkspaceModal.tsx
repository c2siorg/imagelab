import { useState, useEffect } from "react";
import * as Blockly from "blockly";
import { X, Save, Trash2, FolderOpen, Layout } from "lucide-react";
import { useWorkspaceStore } from "../store/workspaceStore";
import { usePipelineStore } from "../store/pipelineStore";

interface WorkspaceModalProps {
  workspace: Blockly.WorkspaceSvg | null;
  onClose: () => void;
}

export default function WorkspaceModal({ workspace, onClose }: WorkspaceModalProps) {
  const { workspaces, loadWorkspaces, saveWorkspace, deleteWorkspace } = useWorkspaceStore();
  const { reset, clearImage } = usePipelineStore();
  const [saveName, setSaveName] = useState("");

  useEffect(() => {
    loadWorkspaces();
  }, [loadWorkspaces]);

  const handleSave = () => {
    if (!saveName.trim() || !workspace) return;
    const data = Blockly.serialization.workspaces.save(workspace);
    saveWorkspace(saveName.trim(), data);
    setSaveName("");
  };

  const handleLoad = (templateData: Record<string, unknown>) => {
    if (!workspace) return;

    if (workspace.getAllBlocks(false).length > 0) {
      if (
        !window.confirm(
          "Loading this workspace will clear your current blocks and uploaded image. Continue?",
        )
      ) {
        return;
      }
    }

    clearImage();
    reset();
    workspace.clear();
    Blockly.serialization.workspaces.load(templateData, workspace);
    onClose();
  };

  const handleDelete = (id: string) => {
    if (window.confirm("Are you sure you want to delete this workspace?")) {
      deleteWorkspace(id);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md flex flex-col max-h-[85vh]">
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <div className="flex items-center gap-2 text-gray-800">
            <Layout className="w-5 h-5 text-indigo-600" />
            <h2 className="font-semibold text-lg">Workspaces</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
            title="Close"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-4 border-b border-gray-100 bg-gray-50 flex flex-col gap-3">
          <label className="text-sm font-medium text-gray-700">Save Current Pipeline</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              placeholder="e.g. Edge Detection Setup"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500"
              onKeyDown={(e) => e.key === "Enter" && handleSave()}
            />
            <button
              onClick={handleSave}
              disabled={!saveName.trim() || !workspace}
              className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save size={16} />
              Save
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {workspaces.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-sm">
              <FolderOpen className="w-10 h-10 mx-auto text-gray-300 mb-2" />
              <p>No saved workspaces yet.</p>
              <p className="text-xs mt-1">Save your current pipeline above.</p>
            </div>
          ) : (
            <div className="space-y-1">
              {workspaces.map((ws) => (
                <div
                  key={ws.id}
                  className="group flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 border border-transparent hover:border-gray-200 transition-all"
                >
                  <div className="flex flex-col min-w-0 pr-4">
                    <span className="font-medium text-sm text-gray-800 truncate">{ws.name}</span>
                    <span className="text-xs text-gray-500">
                      {new Date(ws.createdAt).toLocaleDateString()}{" "}
                      {new Date(ws.createdAt).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleLoad(ws.data)}
                      className="px-3 py-1.5 bg-white border border-gray-300 flex items-center gap-1.5 text-gray-700 rounded-md text-xs font-medium hover:bg-gray-50 hover:text-indigo-600 hover:border-indigo-200 transition-colors"
                    >
                      Load
                    </button>
                    <button
                      onClick={() => handleDelete(ws.id)}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                      title="Delete Workspace"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
