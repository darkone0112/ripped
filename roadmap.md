────────────────────────
RIPPED – Development Codex
────────────────────────

Goal:  
Terminal-only YouTube downloader that uses yt-dlp + ffmpeg under the hood, with:

- audio mode → mp3  
- video mode → mp4 (audio + video merged)  
- simple CLI:  
  ripped <mode> <quality> <url>  

Later: optional web UI on top of the core logic.

────────────────────────
0. Project Skeleton
────────────────────────

[ ] Create project folder: ripped/  
[ ] Initialize git repository  
[ ] Create virtualenv (or Poetry / pipenv)  
[ ] Add basic files:
    [ ] README.md
    [ ] LICENSE
    [ ] .gitignore
    [ ] requirements.txt

Recommended Python structure:

- ripped/
  - main.py              (entry point / CLI)
  - cli/
    - parser.py          (argument parsing)
  - core/
    - downloader.py      (yt-dlp logic)
    - ffmpeg_tools.py    (merging / conversion)
  - config/
    - settings.py        (defaults, paths)
  - utils/
    - logger.py          (logging helper)
  - tests/
    - test_basic.py

────────────────────────
1. Tooling + Dependencies
────────────────────────

[ ] Install ffmpeg at system level (apt, pacman, choco, etc.)  
[ ] Install yt-dlp (system or Python)

requirements.txt (minimum):

[ ] Add:
    - yt-dlp
    - rich (optional, for nicer CLI output)
    - colorama or similar (optional)

[ ] Verify:
    - `ffmpeg` is in PATH
    - `yt-dlp` works standalone: `yt-dlp <url>`

────────────────────────
2. CLI Design (RIPPED command)
────────────────────────

Desired usage:

- Video download:
  ripped video max https://youtu.be/xxxx
  ripped video 1080 https://youtu.be/xxxx

- Audio download:
  ripped audio max https://youtu.be/xxxx

Arguments:

- mode        → "video" or "audio"
- quality     → "max" or numeric (720, 1080, etc.)
- url         → YouTube URL

Tasks:

[ ] main.py:
    [ ] parse sys.argv (later switch to argparse)
    [ ] validate mode (video/audio)
    [ ] validate quality (max or integer)
    [ ] validate URL (basic check: starts with http)

[ ] cli/parser.py:
    [ ] Implement small helper to parse and normalize:
        - mode_lower
        - quality (convert "max" to None or special value)
        - url

[ ] Decide on exit codes:
    [ ] 0 = OK
    [ ] 1 = user error (bad args)
    [ ] 2 = download error
    [ ] 3 = ffmpeg error

────────────────────────
3. Core Logic – yt-dlp integration
────────────────────────

Purpose:  
Use yt-dlp to get the best matching audio/video streams, and optionally let it download them.

In core/downloader.py:

[ ] Implement function: get_video_info(url)

Pseudo:

- Use yt_dlp.YoutubeDL with:
  - quiet = True
  - skip_download = True
- Call extract_info(url, download=False)
- Return:
  - title
  - duration
  - available formats
  - suggested filename

[ ] Implement function: build_format_string(mode, quality)

Rules:

- If mode == "video":
  - quality == "max" → "bestvideo+bestaudio/best"
  - quality is number (e.g. 720) → "bestvideo[height<=720]+bestaudio/best"
- If mode == "audio":
  - ignore resolution; use "bestaudio/best"

[ ] Implement function: download_with_ytdlp(url, format_str, output_template)

- ydl_opts:
  - format: format_str
  - outtmpl: output_template (e.g. "%(title)s.%(ext)s")
  - quiet: True
- Return:
  - paths of downloaded file(s)
  - chosen filename

────────────────────────
4. Core Logic – ffmpeg tools
────────────────────────

In core/ffmpeg_tools.py:

Audio (mp3):

[ ] convert_to_mp3(input_path, output_path)

- ffmpeg command:
  ffmpeg -y -i input_path -vn -codec:a libmp3lame -b:a 192k output_path

Video (mp4 mux):

Option A (easy): yt-dlp handles merging  
Option B (manual): use ffmpeg

[ ] merge_audio_video(video_path, audio_path, output_path)

- ffmpeg command:
  ffmpeg -y -i video_path -i audio_path -c:v copy -c:a aac output_path

────────────────────────
5. Application Flow (Mode: video)
────────────────────────

End-to-end checklist:

[ ] Parse arguments: mode="video", quality, url  
[ ] Build format string with build_format_string("video", quality)  
[ ] Call download_with_ytdlp(url, format_str, output_template)  
[ ] Receive output file path (final mp4 or temp files)  
[ ] Print confirmation:
    - final path
    - resolution used
    - size (optional using os.path.getsize)

Optional later:

[ ] Support specifying output directory  
[ ] Support custom filename template  
[ ] Support dry-run (only show available formats)

────────────────────────
6. Application Flow (Mode: audio)
────────────────────────

Checklist:

[ ] Parse arguments: mode="audio", quality, url  
[ ] Build format string: "bestaudio/best"  
[ ] Download audio-only using yt-dlp  
[ ] Convert downloaded file to mp3 with convert_to_mp3  
[ ] Optionally delete original audio file  
[ ] Print:
    - final mp3 path
    - bitrate
    - size

────────────────────────
7. Error Handling + Logging
────────────────────────

In utils/logger.py:

[ ] Simple logger wrapper:
    - log_info(message)
    - log_error(message)
    - log_debug(message) (optional)

Error cases:

[ ] Missing arguments  
[ ] Invalid mode  
[ ] Invalid quality  
[ ] Invalid URL  
[ ] yt-dlp extraction failure  
[ ] ffmpeg not found  
[ ] ffmpeg failure

For each:

[ ] Print friendly error  
[ ] Exit with appropriate code  

────────────────────────
8. Configuration + Defaults
────────────────────────

In config/settings.py:

[ ] Default output directory (./downloads)  
[ ] Default audio bitrate (192k)  
[ ] Default format mappings:
    - video_max_format = "bestvideo+bestaudio/best"
    - audio_default_format = "bestaudio/best"

Later:

[ ] Optional config file: ripped.toml or ripped.json  
[ ] User overrides:
    - output dir
    - default quality
    - default audio bitrate

────────────────────────
9. Testing
────────────────────────

tests/test_basic.py:

[ ] Test argument parsing  
[ ] Test build_format_string  
[ ] Test get_video_info with a known safe URL  
[ ] Test download_with_ytdlp (small clip)  
[ ] Test mp3 conversion

Manual tests:

[ ] Different URLs  
[ ] Different qualities  
[ ] Audio-only cases  

────────────────────────
10. Packaging & Distribution
────────────────────────

[ ] setup.cfg or pyproject.toml  
[ ] console_scripts entry point:
    - "ripped = ripped.main:main"

[ ] pip install -e . (local install)  
[ ] Verify global command: `ripped ...` works

Later:

[ ] Push to GitHub  
[ ] Optional: publish to PyPI  

────────────────────────
11. Future: Web UI Layer
────────────────────────

Backend:

[ ] FastAPI or Flask  
[ ] Endpoint POST /download  
[ ] Return job ID  
[ ] Optional background worker (Celery/Redis)

Frontend:

[ ] Minimal HTML form  
[ ] Mode dropdown  
[ ] Quality dropdown  
[ ] Show logs / progress  

Later:

[ ] Vue/React frontend  
[ ] Dashboard for queued jobs  
[ ] Thumbnail preview, metadata extraction  

────────────────────────
12. Cosmetic / Identity
────────────────────────

Optional:

[ ] CLI ASCII banner:
    RIPPED
    Ripped Is Pulling Everything Down

[ ] README sections:
    - What is RIPPED
    - Features
    - Install
    - Usage
    - Examples
    - Roadmap

────────────────────────


13. MP4 Compatibility Layer
---------------------------

Goal: ensure everything lands as Resolve-friendly .mp4 with AAC audio.

[ ] Add CLI mode ipped convert <path> to scan a file or directory (recursive) for .webm/.mkv, convert each to .mp4 in-place, and delete originals on success.  
[ ] Hook conversion into download flows so single and bulk downloads automatically run the converter after each item.  
[ ] Handle ffmpeg absence gracefully (clear error), and log per-file results plus a summary counter.  
[ ] Document the new mode and auto-conversion behavior in README with examples.
