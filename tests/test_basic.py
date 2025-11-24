import pytest

from ripped.cli.parser import parse_args
from ripped.core.downloader import build_format_string


def test_parse_args_valid_max_quality():
    parsed = parse_args(["video", "max", "https://example.com"])
    assert parsed.mode == "video"
    assert parsed.quality is None
    assert parsed.url == "https://example.com"


def test_parse_args_numeric_quality():
    parsed = parse_args(["audio", "128", "http://example.com"])
    assert parsed.mode == "audio"
    assert parsed.quality == 128


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["video"],
        ["video", "max"],
        ["invalid", "max", "http://example.com"],
        ["video", "bad", "http://example.com"],
        ["video", "720", "not-a-url"],
    ],
)
def test_parse_args_invalid(argv):
    with pytest.raises(ValueError):
        parse_args(argv)


def test_build_format_string_video_max():
    assert build_format_string("video", None) == "bestvideo+bestaudio/best"


def test_build_format_string_video_with_height():
    assert build_format_string("video", 720) == "bestvideo[height<=720]+bestaudio/best"


def test_build_format_string_audio():
    assert build_format_string("audio", None) == "bestaudio/best"

