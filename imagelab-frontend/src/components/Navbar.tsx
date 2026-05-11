import { Sun, Moon } from "lucide-react";

interface NavbarProps {
  isDark: boolean;
  onToggleDark: () => void;
}

export default function Navbar({ isDark, onToggleDark }: NavbarProps) {
  return (
    <nav className="h-12 flex items-center px-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
      <div className="flex items-center gap-2">
        <img src="/logo.svg" alt="ImageLab logo" width={24} height={24} />
        <h1 className="text-lg font-bold text-gray-800 dark:text-gray-100">ImageLab</h1>
      </div>
      <div className="ml-auto">
        <button
          type="button"
          onClick={onToggleDark}
          aria-pressed={isDark}
          title={isDark ? "Switch to light mode" : "Switch to dark mode"}
          aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
          className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 transition-colors"
        >
          {isDark ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </nav>
  );
}
