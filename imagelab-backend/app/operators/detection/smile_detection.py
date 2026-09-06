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
        draw_face_boxes = bool(self.params.get("drawFaceBoxes", False))
        
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
        
        # Normalize input to grayscale for detection, preserve original for drawing
        original = image.copy()
        
        if len(image.shape) == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif len(image.shape) == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        elif len(image.shape) == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
        elif len(image.shape) == 2:
            gray = image.copy()
        else:
            raise ValueError(f"Unsupported image shape {image.shape}.")
        
        # Ensure uint8 format
        if gray.dtype != np.uint8:
            if np.issubdtype(gray.dtype, np.floating):
                gray = (gray * 255.0 if gray.max() <= 1.0 else gray).clip(0, 255).astype(np.uint8)
            elif gray.dtype == np.uint16:
                gray = (gray >> 8).astype(np.uint8)
            else:
                gray = gray.astype(np.uint8)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=(min_width, min_height)
        )
        
        # No faces detected - return original image unchanged
        if len(faces) == 0:
            return original
        
        # Prepare result canvas (convert grayscale to BGR if needed for colored boxes)
        result = original.copy()
        if len(result.shape) == 2 or (len(result.shape) == 3 and result.shape[2] == 1):
            result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            draw_color = box_color
        elif len(result.shape) == 3 and result.shape[2] == 4:
            draw_color = (*box_color, 255)
        else:
            draw_color = box_color
        
        smile_detected = False
        
        # Detect smiles within each face's lower region
        for (x, y, w, h) in faces:
            # Define the lower portion of the face for smile detection
            roi_y_start = y + int(h * SMILE_ROI_LOWER_FRACTION)
            roi_height = h - int(h * SMILE_ROI_LOWER_FRACTION)
            
            # Extract the smile search region
            smile_roi = gray[roi_y_start:y + h, x:x + w]
            
            # Detect smiles in this ROI
            smiles = self.smile_cascade.detectMultiScale(
                smile_roi,
                scaleFactor=scale_factor,
                minNeighbors=min_neighbors,
                minSize=(min_width // 2, min_height // 2)  # Smiles are typically smaller
            )
            
            # Draw smile bounding boxes (adjusted to global coordinates)
            for (sx, sy, sw, sh) in smiles:
                global_sx = x + sx
                global_sy = roi_y_start + sy
                cv2.rectangle(result, (global_sx, global_sy), (global_sx + sw, global_sy + sh), draw_color, thickness)
                smile_detected = True
            
            # Optionally draw face boxes
            if draw_face_boxes:
                cv2.rectangle(result, (x, y), (x + w, y + h), draw_color, thickness)
        
        # If no smiles detected but faces were found, return original unchanged
        # (unless user wants face boxes drawn)
        if not smile_detected and not draw_face_boxes:
            return original
        
        return result
