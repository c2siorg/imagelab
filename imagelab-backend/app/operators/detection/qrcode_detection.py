import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


class QRCodeDetection(BaseOperator):
    """Detect and decode QR codes in an image.

    Localizes 2D QR codes using OpenCV's built-in QRCodeDetector, outlines them
    with a customizable bounding polygon, marks corner vertices, and optionally
    draws the decoded payload as an overlaid label.

    Includes automatic quiet-zone border padding and Otsu binarization fallbacks
    to reliably detect tightly cropped QR codes, anti-aliased screenshots, and low-contrast codes.

    If no QR codes are found, returns the input image unchanged.
    Grayscale inputs are promoted to BGR so colored annotations can be rendered.
    BGRA inputs preserve their alpha channel.
    """

    def __init__(self, params: dict):
        super().__init__(params)
        self.detector = cv2.QRCodeDetector()

    def _try_detect(self, g: np.ndarray) -> list[tuple[str, np.ndarray]]:
        """Single detection pass attempting multi-detection and single-detection decode."""
        ret, decoded_info, points, _ = self.detector.detectAndDecodeMulti(g)
        if ret and points is not None and len(points) > 0:
            res = [
                (str(text), np.asarray(p, dtype=np.float32).reshape(-1, 2))
                for text, p in zip(decoded_info, points, strict=False)
                if len(np.asarray(p, dtype=np.float32).reshape(-1, 2)) == 4 and text
            ]
            if res:
                return res

        text, single_pts, _ = self.detector.detectAndDecode(g)
        if single_pts is not None and len(single_pts) > 0 and text:
            p_arr = np.asarray(single_pts, dtype=np.float32).reshape(-1, 2)
            if len(p_arr) == 4:
                return [(str(text), p_arr)]

        return []

    def _detect_candidates(self, gray: np.ndarray) -> list[tuple[str, np.ndarray]]:
        """Multi-pass detection: handles raw image, quiet-zone padding, and binarized screen snips."""
        h, w = gray.shape[:2]

        # Pass 1: Raw grayscale
        cand = self._try_detect(gray)
        if cand:
            return cand

        # Pass 2: White quiet-zone margin padding (essential for tightly-cropped images and screenshots)
        pad = max(24, int(min(h, w) * 0.1))
        padded_gray = cv2.copyMakeBorder(gray, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)
        pad_cand = self._try_detect(padded_gray)
        if pad_cand:
            return [(t, np.clip(p - pad, [0, 0], [w - 1, h - 1])) for t, p in pad_cand]

        # Pass 3: Otsu binarization + padding (recovers anti-aliased or low-contrast screen captures)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        padded_thresh = cv2.copyMakeBorder(thresh, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)
        t_cand = self._try_detect(padded_thresh)
        if t_cand:
            return [(t, np.clip(p - pad, [0, 0], [w - 1, h - 1])) for t, p in t_cand]

        return []

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None:
            raise ValueError("Input image cannot be None")

        if not (len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(f"Unsupported image shape {image.shape}.")

        if image.size == 0 or image.shape[0] == 0 or image.shape[1] == 0:
            return image.copy()

        # Extract parameters
        raw_box_color = self.params.get("boxColor", "#00e676")
        box_color = hex_to_bgr(raw_box_color)

        raw_thickness = self.params.get("thickness", 3)
        try:
            thickness = int(raw_thickness)
        except (TypeError, ValueError) as err:
            raise ValueError(f"Invalid thickness: {raw_thickness}") from err

        if thickness < 1 or thickness > 10:
            raise ValueError(f"thickness must be between 1 and 10, got {thickness}")

        draw_label = self.params.get("drawLabel", True)
        if isinstance(draw_label, str):
            draw_label = draw_label.strip().upper() in ("TRUE", "1", "YES")

        raw_text_color = self.params.get("textColor", "#ffffff")
        text_color = hex_to_bgr(raw_text_color)

        # Normalize to uint8 for QR detection
        if image.dtype != np.uint8:
            if np.issubdtype(image.dtype, np.floating):
                norm_image = (image * 255.0 if image.max() <= 1.0 else image).clip(0, 255).astype(np.uint8)
            elif image.dtype == np.uint16:
                norm_image = (image >> 8).astype(np.uint8)
            else:
                norm_image = image.astype(np.uint8)
        else:
            norm_image = image.copy()

        # Build grayscale copy for detection
        if len(norm_image.shape) == 2:
            gray = norm_image
        elif len(norm_image.shape) == 3 and norm_image.shape[2] == 1:
            gray = norm_image[:, :, 0]
        elif len(norm_image.shape) == 3 and norm_image.shape[2] == 3:
            gray = cv2.cvtColor(norm_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cv2.cvtColor(norm_image, cv2.COLOR_BGRA2GRAY)

        detected_list = self._detect_candidates(gray)

        # If no QR codes found, return image unchanged
        if not detected_list:
            return image.copy()

        # Canvas preparation: promote 1-channel / Grayscale to 3-channel BGR
        if len(image.shape) == 2:
            canvas = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif len(image.shape) == 3 and image.shape[2] == 1:
            canvas = cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR)
        else:
            canvas = image.copy()

        is_bgra = len(canvas.shape) == 3 and canvas.shape[2] == 4
        poly_color = (*box_color, 255) if is_bgra else box_color
        txt_draw_color = (*text_color, 255) if is_bgra else text_color

        for text, pts in detected_list:
            pts_int = pts.astype(np.int32)
            cv2.polylines(
                canvas,
                [pts_int],
                isClosed=True,
                color=poly_color,
                thickness=thickness,
                lineType=cv2.LINE_AA,
            )

            # Draw corner vertices
            corner_radius = max(3, thickness + 1)
            for pt in pts_int:
                cv2.circle(
                    canvas,
                    (int(pt[0]), int(pt[1])),
                    corner_radius,
                    poly_color,
                    -1,
                    lineType=cv2.LINE_AA,
                )

            if draw_label:
                label_text = f"QR: {text}" if text else "QR Code"
                if len(label_text) > 35:
                    label_text = label_text[:32] + "..."

                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.45
                font_thick = 1
                (lw, lh), baseline = cv2.getTextSize(label_text, font, font_scale, font_thick)

                # Determine top anchor point
                top_idx = int(np.argmin(pts[:, 1]))
                top_x = int(pts[top_idx, 0])
                top_y = int(pts[top_idx, 1])

                label_h = lh + baseline + 8
                # If there's enough room above the QR code, position above; otherwise place inside top
                if top_y >= label_h + 2:
                    bg_y1 = top_y - label_h
                    bg_y2 = top_y - 2
                else:
                    bg_y1 = min(canvas.shape[0] - label_h, top_y + 4)
                    bg_y2 = bg_y1 + label_h

                bg_x1 = max(0, min(canvas.shape[1] - lw - 8, top_x))
                bg_x2 = min(canvas.shape[1], bg_x1 + lw + 8)

                # Draw label background box
                bg_color = (30, 30, 30, 255) if is_bgra else (30, 30, 30)
                cv2.rectangle(canvas, (bg_x1, bg_y1), (bg_x2, bg_y2), bg_color, -1)
                text_org = (bg_x1 + 4, bg_y2 - baseline - 2)
                cv2.putText(
                    canvas,
                    label_text,
                    text_org,
                    font,
                    font_scale,
                    txt_draw_color,
                    font_thick,
                    lineType=cv2.LINE_AA,
                )

        return canvas
