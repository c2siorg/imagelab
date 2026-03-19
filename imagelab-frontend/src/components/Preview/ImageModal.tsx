import { useEffect } from "react";
import { X } from "lucide-react";

interface ImageModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageSrc: string;
}

export default function ImageModal({ isOpen, onClose, imageSrc }: ImageModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "auto";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <button
        onClick={onClose}
        className="absolute top-4 right-4 p-2 text-white/70 hover:text-white transition-colors bg-black/20 hover:bg-black/40 rounded-full"
        aria-label="Close"
      >
        <X size={24} />
      </button>

      <div className="w-full h-full flex items-center justify-center p-4" onClick={onClose}>
        <img
          src={imageSrc}
          alt="Full screen preview"
          className="max-w-full max-h-full object-contain cursor-default"
          onClick={(e) => e.stopPropagation()}
        />
      </div>
    </div>
  );
}
