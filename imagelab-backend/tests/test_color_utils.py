import pytest

from app.utils.color import hex_to_bgr


def test_valid_hex_with_hash():
    assert hex_to_bgr("#ff0000") == (0, 0, 255)


def test_valid_hex_without_hash():
    assert hex_to_bgr("ff0000") == (0, 0, 255)


def test_hex_is_case_insensitive():
    assert hex_to_bgr("#FF00aa") == (170, 0, 255)


def test_black_hex():
    assert hex_to_bgr("#000000") == (0, 0, 0)


def test_white_hex():
    assert hex_to_bgr("#ffffff") == (255, 255, 255)


@pytest.mark.parametrize("invalid_hex", ["#fff", "", "#zzzzzz", "#ff0000ff", "##abc123"])
def test_invalid_hex_strings_raise_value_error(invalid_hex):
    with pytest.raises(ValueError, match="Expected format"):
        hex_to_bgr(invalid_hex)


def test_none_raises_type_error():
    with pytest.raises(TypeError, match="hex_to_bgr expects a str"):
        hex_to_bgr(None)
