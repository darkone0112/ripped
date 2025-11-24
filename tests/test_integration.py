"""
Optional integration tests that hit the network and require ffmpeg.

To run:
RIPPED_RUN_INTEGRATION=1 pytest tests/test_integration.py
Optionally set RIPPED_TEST_CLIP_URL to override the test clip URL.
"""
import os
import shutil

import pytest

try:
    import yt_dlp  # noqa: F401
except ImportError:
    yt_dlp = None  # type: ignore


RUN_INTEGRATION = os.getenv("RIPPED_RUN_INTEGRATION") == "1"
TEST_CLIP_URL = os.getenv("RIPPED_TEST_CLIP_URL", "https://www.youtube.com/watch?v=BaW_jenozKc")


@pytest.mark.skipif(not RUN_INTEGRATION, reason="Integration tests require RIPPED_RUN_INTEGRATION=1")
def test_audio_download_and_convert(tmp_path):
    if yt_dlp is None:
        pytest.skip("yt-dlp not installed")
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not available in PATH")

    from ripped.core.downloader import build_format_string, download_with_ytdlp
    from ripped.core.ffmpeg_tools import convert_to_mp3

    fmt = build_format_string("audio", None)
    output_template = str(tmp_path / "%(title)s.%(ext)s")
    result = download_with_ytdlp(TEST_CLIP_URL, fmt, output_template)
    downloaded = result["filepath"]
    mp3_path = downloaded.with_suffix(".mp3")

    convert_to_mp3(downloaded, mp3_path)

    assert mp3_path.exists()
