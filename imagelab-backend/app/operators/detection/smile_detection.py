import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr

# ROI fraction for smile detection within detected faces
SMILE_ROI_LOWER_FRACTION = 0.6


class SmileDetection(BaseOperator):
    """Detect smiles using Haar cascades.

    First detects faces, then searches for smiles only in the lower portion
    of each detected face to reduce false positives.
    """

    def __init__(self, params: dict):
        super().__init__(params)

        # Load Haar cascade classifiers
        cascade_path = cv2.data.haarcascades
        face_cascade_path = f"{cascade_path}haarcascade_frontalface_default.xml"
        smile_cascade_path = f"{cascade_path}haarcascade_smile.xml"

        self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
        self.smile_cascade = cv2.CascadeClassifier(smile_cascade_path)

        if self.face_cascade.empty():
            raise ValueError(f"Failed to load face cascade from {face_cascade_path}")
        if self.smile_cascade.empty():
            raise ValueError(f"Failed to load smile cascade from {smile_cascade_path}")

    def compute(self, image: np.ndarray) -> np.ndarray:
        # Extract and validate parameters
        scale_factor = float(self.params.get("scaleFactor", 1.1))
        min_neighbors = int(self.params.get("minNeighbors", 5))
        min_width = int(self.params.get("minWidth", 30))
        min_height = int(self.params.get("minHeight", 30))
        box_color = hex_to_bgr(self.params.get("rgbcolors_input", "#00ff00"))
        thickness = int(self.params.get("thickness", 2))
        # Blockly serializes checkboxes as string 'TRUE'/'FALSE', not boolean
        draw_face_boxes_raw = self.params.get("drawFaceBoxes", False)
        draw_face_boxes = (
            draw_face_boxes_raw == "TRUE" if isinstance(draw_face_boxes_raw, str) else bool(draw_face_boxes_raw)
        )

        # Validate parameters
        if scale_factor < 1.01 or scale_factor > 2.0:
            raise ValueError(f"scaleFactor must be between 1.01 and 2.0, got {scale_factor}")
        if min_neighbors < 1 or min_neighbors > 20:
            raise ValueError(f"minNeighbors must be between 1 and 20, got {min_neighbors}")
        if min_width < 10 or min_width > 500:
            raise ValueError(f"minWidth must be between 10 and 500, got {min_width}")
        if min_height < 10 or min_height > 500:
            raise ValueError(f"minHeight must be between 10 and 500, got {min_height}")
        if thickness < 1 or thickness > 10:
            raise ValueError(f"thickness must be between 1 and 10, got {thickness}")

        # Ensure input shape is valid
        if not (len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(f"Unsupported image shape {image.shape}.")

        # Normalize input to uint8 so every return path produces a valid uint8 image
        if image.dtype != np.uint8:
            if np.issubdtype(image.dtype, np.floating):
                norm_image = (image * 255.0 if image.max() <= 1.0 else image).clip(0, 255).astype(np.uint8)
            elif image.dtype == np.uint16:
                norm_image = (image >> 8).astype(np.uint8)
            else:
                norm_image = image.astype(np.uint8)
        else:
            norm_image = image.copy()

        # Build grayscale image for Haar cascade detection and uint8 canvas for drawing/returning.
        # Single-channel/grayscale inputs are promoted to BGR so colored boxes can be drawn.
        face_color_bgr = (0, 100, 255) if box_color == (255, 100, 0) else (255, 100, 0)
        if len(norm_image.shape) == 2:
            gray = norm_image
            canvas = cv2.cvtColor(norm_image, cv2.COLOR_GRAY2BGR)
            draw_color = box_color
            face_draw_color = face_color_bgr
        elif len(norm_image.shape) == 3 and norm_image.shape[2] == 1:
            gray = norm_image[:, :, 0]
            canvas = cv2.cvtColor(norm_image[:, :, 0], cv2.COLOR_GRAY2BGR)
            draw_color = box_color
            face_draw_color = face_color_bgr
        elif len(norm_image.shape) == 3 and norm_image.shape[2] == 3:
            gray = cv2.cvtColor(norm_image, cv2.COLOR_BGR2GRAY)
            canvas = norm_image.copy()
            draw_color = box_color
            face_draw_color = face_color_bgr
        else:  # 4-channel BGRA
            gray = cv2.cvtColor(norm_image, cv2.COLOR_BGRA2GRAY)
            canvas = norm_image.copy()
            draw_color = (*box_color, 255)
            face_draw_color = (*face_color_bgr, 255)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=scale_factor, minNeighbors=min_neighbors, minSize=(min_width, min_height)
        )

        # No faces detected - return normalized canvas
        if len(faces) == 0:
            return canvas

        smile_detected = False

        # Detect smiles within each face's lower region
        for x, y, w, h in faces:
            # Define the lower portion of the face for smile detection
            roi_y_start = y + int(h * SMILE_ROI_LOWER_FRACTION)

            # Extract the smile search region (lower 60% of face)
            smile_roi = gray[roi_y_start : y + h, x : x + w]

            # Detect smiles in this ROI
            smiles = self.smile_cascade.detectMultiScale(
                smile_roi,
                scaleFactor=scale_factor,
                minNeighbors=min_neighbors,
                minSize=(min_width // 2, min_height // 2),  # Smiles are typically smaller
            )

            # Draw smile bounding boxes (adjusted to global coordinates)
            for sx, sy, sw, sh in smiles:
                global_sx = x + sx
                global_sy = roi_y_start + sy
                cv2.rectangle(canvas, (global_sx, global_sy), (global_sx + sw, global_sy + sh), draw_color, thickness)
                smile_detected = True

            # Optionally draw face boxes (using a distinct color so they differ from smile boxes)
            if draw_face_boxes:
                cv2.rectangle(canvas, (x, y), (x + w, y + h), face_draw_color, thickness)

        # If no smiles detected but faces were found, return normalized canvas unchanged
        # (unless user wants face boxes drawn)
        if not smile_detected and not draw_face_boxes:
            return canvas

        return canvas
