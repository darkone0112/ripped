import pytest

from ripped.cli.parser import parse_args
from ripped.core.downloader import build_format_string


def test_parse_args_valid_max_quality():
    parsed = parse_args(["video", "max", "https://example.com"])
    assert parsed.mode == "video"
    assert parsed.quality is None
    assert parsed.url == "https://example.com"
    assert parsed.path is None


def test_parse_args_numeric_quality():
    parsed = parse_args(["audio", "128", "http://example.com"])
    assert parsed.mode == "audio"
    assert parsed.quality == 128
    assert parsed.url == "http://example.com"
    assert parsed.path is None


def test_parse_args_convert(tmp_path):
    target = tmp_path / "sample.webm"
    target.write_text("placeholder")
    parsed = parse_args(["convert", str(target)])
    assert parsed.mode == "convert"
    assert parsed.quality is None
    assert parsed.url is None
    assert parsed.path == str(target)


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["video"],
        ["video", "max"],
        ["convert"],
        ["convert", "missing-path"],
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
