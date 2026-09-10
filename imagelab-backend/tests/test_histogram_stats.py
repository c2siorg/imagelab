import numpy as np

from app.services.pipeline_executor import analyze_image


def test_calculate_channel_statistics_rgb():
    """Test analyze_image with RGB/BGR images, verify mean/std values per channel."""
    # Create a test RGB image with known values
    # Red channel: all 100, Green channel: all 150, Blue channel: all 200
    rgb_image = np.zeros((50, 50, 3), dtype=np.uint8)
    rgb_image[:, :, 0] = 100  # Blue channel (BGR)
    rgb_image[:, :, 1] = 150  # Green channel
    rgb_image[:, :, 2] = 200  # Red channel

    analysis = analyze_image(rgb_image)

    assert analysis.width == 50
    assert analysis.height == 50
    assert analysis.channels == 3
    assert analysis.dtype == "uint8"
    assert analysis.min == 100.0
    assert analysis.max == 200.0

    # Check mean values (should match the uniform values per channel)
    assert len(analysis.mean) == 3
    assert abs(analysis.mean[0] - 100.0) < 0.01  # Blue
    assert abs(analysis.mean[1] - 150.0) < 0.01  # Green
    assert abs(analysis.mean[2] - 200.0) < 0.01  # Red

    # Check std values (should be 0 for uniform channels)
    assert len(analysis.std) == 3
    assert analysis.std[0] == 0.0
    assert analysis.std[1] == 0.0
    assert analysis.std[2] == 0.0


def test_calculate_channel_statistics_grayscale():
    """Test analyze_image with 2D grayscale images, verify single channel statistics."""
    # Create a grayscale image with varying values
    grayscale_image = np.zeros((100, 80), dtype=np.uint8)
    grayscale_image[:50, :] = 50
    grayscale_image[50:, :] = 150

    analysis = analyze_image(grayscale_image)

    assert analysis.width == 80
    assert analysis.height == 100
    assert analysis.channels == 1
    assert analysis.dtype == "uint8"
    assert analysis.min == 50.0
    assert analysis.max == 150.0

    # For single channel, mean and std should be scalar values
    assert isinstance(analysis.mean, float)
    assert isinstance(analysis.std, float)

    # Due to pixel distribution, mean should be around 100
    assert abs(analysis.mean - 100.0) < 5.0

    # Std should be > 0 since there's variation
    assert analysis.std > 0


def test_zero_variance_image_stats():
    """Test with uniform color images, verify std=0 and correct mean."""
    # Test with white image (all pixels = 255)
    white_image = np.full((30, 40, 3), 255, dtype=np.uint8)
    analysis = analyze_image(white_image)

    assert analysis.width == 40
    assert analysis.height == 30
    assert analysis.channels == 3
    assert analysis.min == 255.0
    assert analysis.max == 255.0

    # All channels should have mean = 255 and std = 0
    assert len(analysis.mean) == 3
    assert all(abs(mean - 255.0) < 0.01 for mean in analysis.mean)
    assert len(analysis.std) == 3
    assert all(std == 0.0 for std in analysis.std)

    # Test with black image (all pixels = 0)
    black_image = np.zeros((20, 30), dtype=np.uint8)
    analysis = analyze_image(black_image)

    assert analysis.channels == 1
    assert analysis.min == 0.0
    assert analysis.max == 0.0
    assert analysis.mean == 0.0
    assert analysis.std == 0.0

    # Test with single-channel uniform image
    uniform_gray = np.full((15, 25), 128, dtype=np.uint8)
    analysis = analyze_image(uniform_gray)

    assert analysis.channels == 1
    assert analysis.min == 128.0
    assert analysis.max == 128.0
    assert abs(analysis.mean - 128.0) < 0.01
    assert analysis.std == 0.0
