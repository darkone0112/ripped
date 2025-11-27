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

### Convert existing videos
Convert all WebM/MKV files to MP4 (AAC audio) in a folder:
```
ripped convert /path/to/folder
```
- Scans recursively for `.webm` and `.mkv`
- Converts each to `.mp4` in place (adds `_converted` suffix if needed)
- Deletes originals after a successful conversion

### Interactive menu
- Run with no args or `python -m ripped.main menu` to open a menu that shows current preferences and options to:
  - Set mode (audio/video)
  - Set quality via presets (max, 360, 480, 720, 1080, 1440, 2160/4K)
  - Download a single URL (press Enter to auto-use clipboard if a URL is copied)
  - Bulk download: on Windows, copied URLs (Ctrl+C) are auto-queued (requires `pyperclip`); type manually if needed; press `q` to start the downloads

### Notes
- This is the first iteration of the working pipeline: parsing, format selection, download, and mp3 conversion are wired, but error handling/logging are still minimal.
- All video downloads auto-convert to MP4 with AAC audio to keep outputs friendly for editors like DaVinci Resolve.
- Requirements: `yt-dlp`, `ffmpeg` in PATH.
- Optional integration test: set `RIPPED_RUN_INTEGRATION=1` (and optionally `RIPPED_TEST_CLIP_URL`) before running pytest to hit a real clip.
