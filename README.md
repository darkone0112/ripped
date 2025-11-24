# RIPPED
Ripped Is Processing, Parsing, Extracting &amp; Downloading

## Usage (initial skeleton)
```
ripped <mode> <quality> <url>
```
- mode: `audio` or `video`
- quality: `max` or an integer (e.g., `720`, `1080`)
- url: YouTube URL

Example:
```
ripped video 1080 https://youtu.be/xxxx
```

### Interactive menu
- Run with no args or `python -m ripped.main menu` to open a menu that shows current preferences and options to:
  - Set mode (audio/video)
  - Set quality via presets (max, 360, 480, 720, 1080, 1440, 2160/4K)
  - Download a single URL (press Enter to auto-use clipboard if a URL is copied)
  - Bulk download: on Windows, copied URLs (Ctrl+C) are auto-queued (requires `pyperclip`); type manually if needed; press `q` to start the downloads

### Notes
- This is the first iteration of the working pipeline: parsing, format selection, download, and mp3 conversion are wired, but error handling/logging are still minimal.
- Requirements: `yt-dlp`, `ffmpeg` in PATH.
- Optional integration test: set `RIPPED_RUN_INTEGRATION=1` (and optionally `RIPPED_TEST_CLIP_URL`) before running pytest to hit a real clip.
