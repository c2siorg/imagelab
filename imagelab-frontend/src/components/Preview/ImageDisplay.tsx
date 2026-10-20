import { useState } from "react";
import ImageModal from "./ImageModal";

interface ImageDisplayProps {
  image: string;
  format: string;
  zoomWidth?: number | null;
  alt?: string;
  imageRef?: React.Ref<HTMLImageElement>;
  children?: React.ReactNode;
}

export default function ImageDisplay({
  image,
  format,
  zoomWidth,
  alt = "Preview",
  imageRef,
  children,
}: ImageDisplayProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const imageSrc = `data:image/${format};base64,${image}`;

  return (
    <>
      <img
        ref={imageRef}
        src={imageSrc}
        alt={alt}
        className={
          zoomWidth
            ? "cursor-zoom-in"
            : "max-w-full max-h-full object-contain cursor-zoom-in hover:opacity-90 transition-opacity"
        }
        style={zoomWidth ? { width: `${zoomWidth}px` } : undefined}
        onClick={() => setIsModalOpen(true)}
      />
      {children}
      <ImageModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} imageSrc={imageSrc} />
    </>
  );
}
