interface ImageDisplayProps {
  image: string;
  format: string;
  zoomWidth?: number | null;
}

export default function ImageDisplay({ image, format, zoomWidth }: ImageDisplayProps) {
  return (
    <img
      src={`data:image/${format};base64,${image}`}
      alt="Preview"
      className={zoomWidth ? '' : 'max-w-full max-h-full object-contain'}
      style={zoomWidth ? { width: `${zoomWidth}px` } : undefined}
    />
  );
}
