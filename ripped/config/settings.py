from pathlib import Path

# Defaults can be extended later with file-based overrides.
DEFAULT_OUTPUT_DIR = Path("downloads")
DEFAULT_AUDIO_BITRATE = "192k"

VIDEO_MAX_FORMAT = "bestvideo+bestaudio/best"
AUDIO_DEFAULT_FORMAT = "bestaudio/best"

# Used by yt-dlp output templating.
DEFAULT_OUTPUT_TEMPLATE = "%(title)s.%(ext)s"

