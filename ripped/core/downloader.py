from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yt_dlp
except ImportError:
    yt_dlp = None  # type: ignore


def _require_yt_dlp() -> None:
    if yt_dlp is None:
        raise RuntimeError("yt-dlp is not installed. Please install it to enable downloads.")


def get_video_info(url: str) -> Dict[str, Any]:
    """Extract metadata for a video without downloading it."""
    _require_yt_dlp()
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[attr-defined]
        info = ydl.extract_info(url, download=False)
    return {
        "title": info.get("title"),
        "duration": info.get("duration"),
        "formats": info.get("formats"),
        "filename": ydl.prepare_filename(info),  # type: ignore[name-defined]
    }


def build_format_string(mode: str, quality: Optional[int]) -> str:
    """Build the yt-dlp format string based on mode and requested quality."""
    mode_lower = mode.lower()
    if mode_lower not in {"audio", "video"}:
        raise ValueError('Mode must be "audio" or "video".')

    if mode_lower == "audio":
        return "bestaudio/best"

    # mode_lower == "video"
    if quality is None:
        return "bestvideo+bestaudio/best"

    return f"bestvideo[height<={quality}]+bestaudio/best"


def download_with_ytdlp(url: str, format_str: str, output_template: str = "%(title)s.%(ext)s") -> Dict[str, Any]:
    """Download content using yt-dlp with the provided format string."""
    _require_yt_dlp()
    ydl_opts = {
        "format": format_str,
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[attr-defined]
        result = ydl.extract_info(url, download=True)
        return {
            "filepath": Path(ydl.prepare_filename(result)),  # type: ignore[name-defined]
            "title": result.get("title"),
            "requested_format": format_str,
        }
