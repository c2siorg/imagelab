import { useState } from "react";
import { Play, Blocks, Zap, Eye } from "lucide-react";

interface LandingPageProps {
  onStart: (dontShowAgain: boolean) => void;
}

export default function LandingPage({ onStart }: LandingPageProps) {
  const [dontShowAgain, setDontShowAgain] = useState(false);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4 sm:p-8">
      <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl border border-gray-100 flex flex-col md:flex-row">
        {/* Left Side: Info & Features */}
        <div className="p-8 md:p-12 flex-1 border-b md:border-b-0 md:border-r border-gray-100 bg-white rounded-t-2xl md:rounded-l-2xl md:rounded-tr-none">
          <div className="mb-8 flex items-center gap-4">
            <img
              src="/logo.svg"
              alt="ImageLab Logo"
              className="w-14 h-14"
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).style.display = "none";
              }}
            />
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">ImageLab</h1>
          </div>

          <p className="text-gray-600 mb-10 text-lg leading-relaxed">
            A powerful, visual environment for building image processing pipelines. Leverage
            industry-standard algorithms without writing a single line of code.
          </p>

          <div className="space-y-7">
            <h2 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
              Key Features
            </h2>

            <div className="flex gap-4">
              <div className="flex-shrink-0 mt-1">
                <div className="w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600">
                  <Blocks size={20} />
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-base mb-1">
                  Block-Based Interface
                </h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  Drag, drop, and connect operations seamlessly on a freeform workspace canvas.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 mt-1">
                <div className="w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600">
                  <Zap size={20} />
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-base mb-1">OpenCV Powered</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  Execute blazing-fast operations including blurring, thresholding, and advanced
                  transforms.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 mt-1">
                <div className="w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600">
                  <Eye size={20} />
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-base mb-1">Real-Time Previews</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  Instantly see the effects of your pipeline steps on the live preview pane.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: Quick Start & Actions */}
        <div className="p-8 md:p-12 w-full md:w-[400px] bg-gray-50 flex flex-col justify-between rounded-b-2xl md:rounded-r-2xl md:rounded-bl-none">
          <div>
            <h2 className="text-xs font-bold text-indigo-900/60 uppercase tracking-widest mb-8">
              Quick Start Guide
            </h2>
            <div className="relative">
              <div
                aria-hidden="true"
                className="absolute left-[11px] top-4 bottom-4 w-[2px] bg-indigo-200/50 z-0"
              ></div>

              <ol className="space-y-8">
                <li className="flex gap-5 relative z-10">
                  <span
                    aria-hidden="true"
                    className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-600 text-white shadow-sm ring-4 ring-gray-50 flex items-center justify-center font-bold text-xs mt-0.5"
                  >
                    1
                  </span>
                  <div>
                    <span className="text-gray-900 block font-medium text-sm mb-1">Read Image</span>
                    <span className="text-sm text-gray-600 leading-snug block">
                      Start by dropping a Read Image block and uploading a photo.
                    </span>
                  </div>
                </li>

                <li className="flex gap-5 relative z-10">
                  <span
                    aria-hidden="true"
                    className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-600 text-white shadow-sm ring-4 ring-gray-50 flex items-center justify-center font-bold text-xs mt-0.5"
                  >
                    2
                  </span>
                  <div>
                    <span className="text-gray-900 block font-medium text-sm mb-1">
                      Build Pipeline
                    </span>
                    <span className="text-sm text-gray-600 leading-snug block">
                      Connect filters, drawing ops, or conversions.
                    </span>
                  </div>
                </li>

                <li className="flex gap-5 relative z-10">
                  <span
                    aria-hidden="true"
                    className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-600 text-white shadow-sm ring-4 ring-gray-50 flex items-center justify-center font-bold text-xs mt-0.5"
                  >
                    3
                  </span>
                  <div>
                    <span className="text-gray-900 block font-medium text-sm mb-1">Execute</span>
                    <span className="text-sm text-gray-600 leading-snug block">
                      Click the Run button to process and view results.
                    </span>
                  </div>
                </li>
              </ol>
            </div>
          </div>

          <div className="mt-12">
            <button
              type="button"
              onClick={() => onStart(dontShowAgain)}
              className="w-full flex items-center justify-center gap-2.5 py-4 px-4 bg-indigo-600 hover:bg-indigo-700 hover:scale-[1.01] active:bg-indigo-800 active:scale-[0.98] text-white rounded-xl font-medium transition-all shadow-lg shadow-indigo-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 mb-6 group text-[15px]"
            >
              <Play size={18} className="group-hover:translate-x-0.5 transition-transform" />
              Enter Workspace
            </button>

            <label className="flex items-center justify-center gap-3 cursor-pointer group">
              <div className="relative flex items-center justify-center">
                <input
                  type="checkbox"
                  checked={dontShowAgain}
                  onChange={(e) => setDontShowAgain(e.target.checked)}
                  className="peer appearance-none w-4 h-4 rounded border-2 border-gray-300 checked:bg-indigo-600 checked:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-all cursor-pointer bg-white"
                />
                <svg
                  aria-hidden="true"
                  className="absolute w-2.5 h-2.5 text-white pointer-events-none opacity-0 peer-checked:opacity-100 transition-opacity"
                  viewBox="0 0 14 10"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M1 5L4.5 8.5L13 1"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <span className="text-sm text-gray-500 group-hover:text-gray-800 transition-colors select-none font-medium">
                Don't show this again
              </span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
