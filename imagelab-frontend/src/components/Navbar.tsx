export default function Navbar() {
  return (
    <nav className="h-12 flex items-center px-4 bg-white border-b border-gray-200 flex-shrink-0">
      <div className="flex items-center gap-2">
        <img src="/logo.svg" alt="ImageLab logo" width={24} height={24} />
        <h1 className="text-lg font-bold text-gray-800">ImageLab</h1>
      </div>
    </nav>
  );
}
