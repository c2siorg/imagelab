import numpy as np

from app.operators.filtering.hough_lines import HoughLines


def test_hough_lines_preserves_shape() -> None:
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    out = HoughLines({}).compute(img)
    assert out.shape == img.shape
    assert np.array_equal(out, img)


def test_hough_lines_detects_and_draws() -> None:
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    for i in range(10, 90):
        img[i, i] = [255, 255, 255]

    out = HoughLines(
        {
            "rho": 1.0,
            "thetaDegrees": 1.0,
            "threshold": 10,
            "minLineLength": 10,
            "maxLineGap": 5,
            "color": "#FF0000",
            "thickness": 1,
        }
    ).compute(img)

    assert out.shape == img.shape
    has_red = np.any(np.all(out == [0, 0, 255], axis=-1))
    assert has_red, "No red pixel found in drawn image"


def test_hough_lines_converts_theta_degrees_to_radians(monkeypatch) -> None:
    captured: dict[str, float | int] = {}

    def fake_hough_lines_p(
        edges: np.ndarray,
        rho: float,
        theta: float,
        threshold: int,
        minLineLength: float,
        maxLineGap: float,
    ) -> None:
        captured["rho"] = rho
        captured["theta"] = theta
        captured["threshold"] = threshold
        captured["minLineLength"] = minLineLength
        captured["maxLineGap"] = maxLineGap
        return None

    monkeypatch.setattr("app.operators.filtering.hough_lines.cv2.HoughLinesP", fake_hough_lines_p)

    image = np.zeros((20, 20, 3), dtype=np.uint8)
    out = HoughLines(
        {
            "rho": 2.0,
            "thetaDegrees": 90.0,
            "threshold": 7,
            "minLineLength": 8,
            "maxLineGap": 9,
        }
    ).compute(image)

    assert np.array_equal(out, image)
    assert captured["rho"] == 2.0
    assert np.isclose(captured["theta"], np.pi / 2)
    assert captured["threshold"] == 7
    assert captured["minLineLength"] == 8.0
    assert captured["maxLineGap"] == 9.0


def test_hough_lines_draws_on_original_image_not_edge_map(monkeypatch) -> None:
    def fake_hough_lines_p(
        edges: np.ndarray,
        rho: float,
        theta: float,
        threshold: int,
        minLineLength: float,
        maxLineGap: float,
    ) -> np.ndarray:
        return np.array([[[2, 2, 8, 2]]], dtype=np.int32)

    monkeypatch.setattr("app.operators.filtering.hough_lines.cv2.HoughLinesP", fake_hough_lines_p)

    image = np.full((12, 12, 3), fill_value=(10, 20, 30), dtype=np.uint8)
    out = HoughLines({"color": "#FF0000", "thickness": 1}).compute(image)

    assert np.array_equal(out[10, 10], image[10, 10])
    assert np.array_equal(out[2, 2], np.array([0, 0, 255], dtype=np.uint8))


def test_hough_lines_grayscale_input_returns_bgr() -> None:
    img = np.zeros((50, 50), dtype=np.uint8)
    for i in range(10, 40):
        img[i, 25] = 255

    out = HoughLines({"threshold": 5, "minLineLength": 5, "color": "#00FF00"}).compute(img)

    assert len(out.shape) == 3
    assert out.shape == (50, 50, 3)
    has_green = np.any(np.all(out == [0, 255, 0], axis=-1))
    assert has_green, "Grayscale image didn't convert and draw green lines"


def test_hough_lines_draws_on_bgra_input(monkeypatch) -> None:
    def fake_hough_lines_p(edges, rho, theta, threshold, minLineLength, maxLineGap):
        return np.array([[[1, 1, 9, 1]]], dtype=np.int32)

    monkeypatch.setattr("app.operators.filtering.hough_lines.cv2.HoughLinesP", fake_hough_lines_p)

    image = np.full((12, 12, 4), fill_value=(10, 20, 30, 255), dtype=np.uint8)
    out = HoughLines({"color": "#FF0000", "thickness": 1}).compute(image)

    assert out.shape[2] in (3, 4), "BGRA input must return a valid image"
    assert out[1, 1, 2] == 255, "Expected red channel 255 at drawn line pixel"
