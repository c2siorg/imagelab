import { useBlocklyWorkspace } from "../hooks/useBlocklyWorkspace";
import Navbar from "./Navbar";
import Toolbar from "./Toolbar";
import Sidebar from "./Sidebar/Sidebar";
import PreviewPane from "./Preview/PreviewPane";
import InfoPane from "./InfoPane";

export default function Layout() {
  const { containerRef, workspace } = useBlocklyWorkspace();

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Navbar />
      <Toolbar workspace={workspace} />
      <div className="flex flex-1 min-h-0">
        <Sidebar workspace={workspace} />
        <div className="flex-1 flex flex-col min-w-0">
          <div ref={containerRef} className="flex-1" />
          <InfoPane />
        </div>
        <PreviewPane />
      </div>
    </div>
  );
}
