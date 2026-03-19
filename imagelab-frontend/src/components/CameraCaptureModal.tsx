import { useEffect, useRef, useState } from "react";
import { Camera, Loader2, RefreshCcw, X } from "lucide-react";
import { usePipelineStore } from "../store/pipelineStore";
import { canvasToBlob } from "../utils/canvas";
import { blobToDataUrl, getImageFormatFromMimeType } from "../utils/imageData";

const DEFAULT_CAPTURE_TYPE = "image/png";

function getCameraErrorMessage(error: unknown): string {
  if (!(error instanceof Error)) {
    return "Unable to access the camera.";
  }

  switch (error.name) {
    case "NotAllowedError":
    case "PermissionDeniedError":
      return "Camera permission was denied. Allow access and try again.";
    case "NotFoundError":
    case "DevicesNotFoundError":
      return "No camera was found on this device.";
    case "NotReadableError":
    case "TrackStartError":
      return "The camera is already in use by another application.";
    case "OverconstrainedError":
    case "ConstraintNotSatisfiedError":
      return "The requested camera settings are not supported on this device.";
    case "AbortError":
      return "Camera startup was interrupted. Please try again.";
    case "SecurityError":
      return "Camera access is blocked in this context.";
    default:
      return error.message || "Unable to access the camera.";
  }
}

function stopStream(stream: MediaStream | null) {
  stream?.getTracks().forEach((track) => track.stop());
}

function createCaptureLabel(date = new Date()): string {
  const value = date.toISOString().replace(/[:.]/g, "-");
  return `camera-capture-${value}.png`;
}

export default function CameraCaptureModal() {
  const { isCameraModalOpen, cameraCaptureHandler, closeCameraModal } = usePipelineStore();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    if (!isCameraModalOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        closeCameraModal();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [closeCameraModal, isCameraModalOpen]);

  useEffect(() => {
    if (!isCameraModalOpen) {
      setError(null);
      setIsLoading(false);
      setIsReady(false);
      setIsCapturing(false);
      stopStream(streamRef.current);
      streamRef.current = null;
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      return undefined;
    }

    if (
      typeof navigator === "undefined" ||
      !navigator.mediaDevices ||
      typeof navigator.mediaDevices.getUserMedia !== "function"
    ) {
      setError("This browser does not support camera capture.");
      return undefined;
    }

    let disposed = false;
    const video = videoRef.current;
    setError(null);
    setIsLoading(true);
    setIsReady(false);

    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: "environment" } },
          audio: false,
        });

        if (disposed) {
          stopStream(stream);
          return;
        }

        streamRef.current = stream;
        stream.getVideoTracks().forEach((track) => {
          track.addEventListener("ended", () => {
            setError("The camera stream ended. Retry to reconnect.");
            setIsReady(false);
          });
        });
        if (!video) {
          stopStream(stream);
          setError("Camera preview could not be initialized.");
          return;
        }

        video.srcObject = stream;
        await video.play();
        setIsReady(true);
      } catch (cameraError) {
        setError(getCameraErrorMessage(cameraError));
      } finally {
        if (!disposed) {
          setIsLoading(false);
        }
      }
    };

    void startCamera();

    return () => {
      disposed = true;
      stopStream(streamRef.current);
      streamRef.current = null;
      if (video) {
        video.srcObject = null;
      }
    };
  }, [isCameraModalOpen, retryKey]);

  const handleClose = () => {
    closeCameraModal();
  };

  const handleRetry = () => {
    stopStream(streamRef.current);
    streamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setError(null);
    setIsReady(false);
    setIsLoading(false);
    setRetryKey((value) => value + 1);
  };

  const handleCapture = async () => {
    const video = videoRef.current;
    if (!video || !cameraCaptureHandler || isCapturing) return;

    if (video.videoWidth <= 0 || video.videoHeight <= 0) {
      setError("Camera is not ready to capture yet.");
      return;
    }

    setIsCapturing(true);
    setError(null);

    try {
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const context = canvas.getContext("2d");

      if (!context) {
        throw new Error("Canvas context is unavailable.");
      }

      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      const blob = await canvasToBlob(canvas, { type: DEFAULT_CAPTURE_TYPE });
      const dataUrl = await blobToDataUrl(blob);
      const [, base64 = ""] = dataUrl.split(",", 2);

      if (!base64) {
        throw new Error("Camera capture returned empty image data.");
      }

      cameraCaptureHandler({
        image: base64,
        format: getImageFormatFromMimeType(blob.type),
        label: createCaptureLabel(),
      });

      handleClose();
    } catch (captureError) {
      setError(
        captureError instanceof Error
          ? captureError.message
          : "Unable to capture an image from the camera.",
      );
    } finally {
      setIsCapturing(false);
    }
  };

  if (!isCameraModalOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 px-4"
      onClick={handleClose}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Capture image from camera"
        className="w-full max-w-3xl overflow-hidden rounded-2xl bg-white shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
          <div className="flex items-center gap-2">
            <Camera size={18} className="text-emerald-600" />
            <h2 className="text-sm font-semibold text-gray-800">Capture Image</h2>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="rounded p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
            aria-label="Close camera"
          >
            <X size={16} />
          </button>
        </div>

        <div className="space-y-4 p-5">
          <div className="relative overflow-hidden rounded-xl bg-gray-950">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="max-h-[70vh] min-h-64 w-full bg-gray-950 object-contain"
              onLoadedMetadata={() => setIsReady(true)}
            />
            {(isLoading || !isReady) && !error && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-gray-950/75 text-white">
                <Loader2 size={22} className="animate-spin" />
                <p className="text-sm">Starting camera…</p>
              </div>
            )}
          </div>

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-gray-500">
              Position the image in frame, then capture it for the `Read Image` block.
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleRetry}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50"
              >
                <RefreshCcw size={14} />
                Retry
              </button>
              <button
                type="button"
                onClick={handleCapture}
                disabled={!isReady || isLoading || isCapturing || !!error}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isCapturing ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Camera size={14} />
                )}
                {isCapturing ? "Capturing..." : "Capture"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
