import base64

import cv2
import numpy as np
import pytest

from app.operators.detection.qrcode_detection import QRCodeDetection
from app.operators.registry import get_operator
from app.services.python_exporter.templates import OPERATOR_TEMPLATES

SAMPLE_QR_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAASwAAAEsAQMAAABDsxw2AAAABlBMVEX///8AAABVwtN+AAAACXBIWXMAAA7EAAAOxAGVKw4b"
    "AAAB3klEQVRoge2avXHDMAyF4VPhkiNolIxmjeZRPIJLFbogxANIyroUbmCreKgY8FOad/ilRd6zm4aJXH/dNTdPO+iDWDL2"
    "wNVkzl/50S3EeZpn9T+I5WPXqoY5BQdzmmql8vN6qa6N2AcxiPWEOhddIB+xs2J2ey+WznCrxD6J9fxWnfd6ALaY8/80SCwB"
    "0zDHyub5zatMuyOWjB2sWOuFw3a8IvZ1zDV9Ti4eNPXIqp4uLrF0LJIYar1bb8zqh4tEfiOWiplGMvmoiCFlDvnEWy8YsVNg"
    "1pjdS78Viyz7ej9aEsvGFON8bFcwpMxr16jzxFKxkdZMLAwpKC4aZrw1ZsRysRogEMtHkj6kWK0XHxXxT4idAMMGTDdPa2iP"
    "oXLpmk5KLBu7uSJNLEyU0pYqCDFPg8RSMR2LLNuuvMhnYvmHxHKxvmlse8WYTWK7spTQlNgpsDZIWkChPUaTgHIjOBDLx0SG"
    "c7THvcqgVSOWiw3ztbA5WxBJFCBiJ8Fuod3+JUV9lhkZT4glY67X7lUxFpI6dlz7ACSWg/Var74NHqOi2eI8sU9h60t7HC9W"
    "CKlje0zs+5i05fxurg+eWDLW8ttsnracl+OrIrFUrCvSf6Dl7XGbGcuxJSD2New9+wM+GwVZ3v1ltAAAAABJRU5ErkJggg=="
)


def _get_sample_qr() -> np.ndarray:
    raw = base64.b64decode(SAMPLE_QR_B64)
    arr = np.frombuffer(raw, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _get_tight_cropped_qr() -> np.ndarray:
    """Returns a QR code tightly cropped to the finder patterns with 0px white margin."""
    img = _get_sample_qr()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ys, xs = np.where(gray < 50)
    return img[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1].copy()


def test_registry_lookup():
    cls = get_operator("detection_qrcodedetection")
    assert cls is QRCodeDetection


def test_detect_qr_code_bgr_and_payload():
    img = _get_sample_qr()
    op = QRCodeDetection({"thickness": 2, "boxColor": "#00e676", "drawLabel": True})
    cands = op._detect_candidates(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    assert len(cands) >= 1
    assert cands[0][0] == "https://github.com/c2siorg/imagelab"

    res = op.compute(img)
    assert res.shape == img.shape
    assert res.dtype == np.uint8
    assert np.count_nonzero(res != img) > 0


def test_quiet_zone_padding_fallback_on_tight_crop():
    """Verify that a tightly-cropped QR code (failing raw OpenCV detection) is decoded via padding."""
    tight = _get_tight_cropped_qr()

    # Confirm raw detector without quiet-zone padding fails
    raw_detector = cv2.QRCodeDetector()
    raw_text, _, _ = raw_detector.detectAndDecode(cv2.cvtColor(tight, cv2.COLOR_BGR2GRAY))
    assert raw_text == ""

    # Confirm operator successfully decodes using quiet-zone padding pass
    op = QRCodeDetection({"thickness": 3, "boxColor": "#00e676", "drawLabel": True})
    cands = op._detect_candidates(cv2.cvtColor(tight, cv2.COLOR_BGR2GRAY))
    assert len(cands) == 1
    assert cands[0][0] == "https://github.com/c2siorg/imagelab"

    res = op.compute(tight)
    assert np.count_nonzero(res != tight) > 0


def test_no_false_positives_on_noisy_or_textured_images():
    """Verify textured and noisy images without a valid QR code return unchanged without false positives."""
    op = QRCodeDetection({})

    # 1. Solid blank image
    blank = np.zeros((100, 100, 3), dtype=np.uint8)
    res_blank = op.compute(blank)
    assert np.array_equal(res_blank, blank)

    # 2. High-contrast checkerboard grid
    checker = np.zeros((200, 200, 3), dtype=np.uint8)
    checker[::10, :] = 255
    checker[:, ::10] = 255
    res_checker = op.compute(checker)
    assert np.array_equal(res_checker, checker)

    # 3. Random noise
    np.random.seed(42)
    noisy = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)
    res_noisy = op.compute(noisy)
    assert np.array_equal(res_noisy, noisy)


def test_detect_qr_code_grayscale_promoted_to_bgr():
    img = _get_sample_qr()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    op = QRCodeDetection({"thickness": 2, "boxColor": "#00e676"})
    res = op.compute(gray)
    assert res.ndim == 3
    assert res.shape[2] == 3
    assert res.shape[:2] == gray.shape[:2]


def test_detect_qr_code_single_channel_3d():
    img = _get_sample_qr()
    gray_3d = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)[:, :, np.newaxis]
    op = QRCodeDetection({"thickness": 2})
    res = op.compute(gray_3d)
    assert res.ndim == 3
    assert res.shape[2] == 3
    assert res.shape[:2] == gray_3d.shape[:2]


def test_detect_qr_code_bgra_preserves_alpha():
    img = _get_sample_qr()
    bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = 200
    op = QRCodeDetection({"thickness": 2, "boxColor": "#00e676"})
    res = op.compute(bgra)
    assert res.shape == bgra.shape
    assert res.shape[2] == 4
    # Preserves 4-channel BGRA representation with unmodified background maintaining alpha
    assert np.any(res[:, :, 3] == 200)


def test_draw_label_toggle():
    img = _get_sample_qr()
    op_with_label = QRCodeDetection({"drawLabel": True, "thickness": 2})
    op_without_label = QRCodeDetection({"drawLabel": False, "thickness": 2})
    res_label = op_with_label.compute(img)
    res_no_label = op_without_label.compute(img)

    assert not np.array_equal(res_label, res_no_label)
    assert np.count_nonzero(res_label != img) > np.count_nonzero(res_no_label != img)


def test_parameter_validation_and_errors():
    op = QRCodeDetection({})
    with pytest.raises(ValueError, match="Input image cannot be None"):
        op.compute(None)

    with pytest.raises(ValueError, match="Unsupported image shape"):
        op.compute(np.zeros((100,), dtype=np.uint8))

    with pytest.raises(ValueError, match="thickness must be between 1 and 10"):
        QRCodeDetection({"thickness": 0}).compute(np.zeros((50, 50, 3), dtype=np.uint8))

    with pytest.raises(ValueError, match="thickness must be between 1 and 10"):
        QRCodeDetection({"thickness": 15}).compute(np.zeros((50, 50, 3), dtype=np.uint8))

    empty = np.zeros((0, 0, 3), dtype=np.uint8)
    res = op.compute(empty)
    assert res.shape == empty.shape


def test_exporter_template_and_parity():
    template_fn = OPERATOR_TEMPLATES.get("detection_qrcodedetection")
    assert template_fn is not None
    code_lines, _ = template_fn({"thickness": 3, "boxColor": "#00e676", "drawLabel": True}, "img")
    assert any("QRCodeDetector" in line for line in code_lines)
    assert any("detectAndDecodeMulti" in line for line in code_lines)
    assert any("copyMakeBorder" in line for line in code_lines)

    # 1. Parity test on clean standard sample image
    sample = _get_sample_qr()
    op = QRCodeDetection({"thickness": 3, "boxColor": "#00e676", "drawLabel": True})
    op_out_sample = op.compute(sample)

    local_scope_sample = {"img": sample.copy(), "cv2": cv2, "np": np}
    exec("\n".join(code_lines), local_scope_sample)
    assert np.array_equal(op_out_sample, local_scope_sample["img"])

    # 2. Parity test on tightly-cropped QR code (exercising quiet-zone fallback in exporter)
    tight = _get_tight_cropped_qr()
    op_out_tight = op.compute(tight)

    local_scope_tight = {"img": tight.copy(), "cv2": cv2, "np": np}
    exec("\n".join(code_lines), local_scope_tight)
    assert np.array_equal(op_out_tight, local_scope_tight["img"])
