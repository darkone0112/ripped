import os
import sys
import time
from pathlib import Path
from subprocess import CalledProcessError

from ripped.cli.parser import ParsedArgs, parse_args
from ripped.cli.parser import _validate_mode as validate_mode
from ripped.cli.parser import _validate_quality as validate_quality
from ripped.cli.parser import _validate_url as validate_url
from ripped.config.settings import (
    DEFAULT_AUDIO_BITRATE,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_TEMPLATE,
)
from ripped.core.converter import convert_to_mp4_in_place, run_bulk_conversion
from ripped.core.downloader import build_format_string, download_with_ytdlp
from ripped.core.ffmpeg_tools import convert_to_mp3
from ripped.utils.logger import clear_log_sink, log_error, log_info, set_log_sink


EXIT_OK = 0
EXIT_USER_ERROR = 1
EXIT_DOWNLOAD_ERROR = 2
EXIT_FFMPEG_ERROR = 3
QUALITY_CHOICES = [None, 360, 480, 720, 1080, 1440, 2160]  # None -> max

try:
    import pyperclip
except ImportError:
    pyperclip = None  # type: ignore
try:
    import msvcrt  # Windows-only
except ImportError:
    msvcrt = None  # type: ignore


def format_quality_label(quality: int | None) -> str:
    return "max" if quality is None else str(quality)


_warned_clipboard = False

def _load_logo() -> str:
    logo_path = Path(__file__).resolve().parent / "logo.txt"
    try:
        return logo_path.read_text(encoding="utf-8").rstrip("\n")
    except OSError:
        return "RIPPED"


MENU_ART = _load_logo()
MENU_WIDTH = max(60, max((len(line) for line in MENU_ART.splitlines()), default=0))
FRAME_EDGE = "▒"
FRAME_FILL = "░"
FRAME_PAD = 4
FRAME_WIDTH = max(MENU_WIDTH + FRAME_PAD, 70)


def read_clipboard() -> str | None:
    global _warned_clipboard
    if pyperclip is None:
        if not _warned_clipboard:
            print("Clipboard unavailable: install pyperclip for auto-capture.")
            _warned_clipboard = True
        return None
    try:
        text = pyperclip.paste()
        return text.strip() if text else None
    except Exception as exc:
        if not _warned_clipboard:
            print(f"Clipboard access failed: {exc}")
            _warned_clipboard = True
        return None


def perform_download(mode: str, quality: int | None, url: str) -> int:
    """Execute a single download based on mode/quality/url."""
    try:
        format_str = build_format_string(mode, quality)
    except ValueError as exc:
        log_error(str(exc))
        return EXIT_USER_ERROR

    log_info(f"Mode: {mode}")
    log_info(f"Quality: {format_quality_label(quality)}")
    log_info(f"URL: {url}")
    log_info(f"Format string: {format_str}")

    output_dir = Path(DEFAULT_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / DEFAULT_OUTPUT_TEMPLATE)

    try:
        download_result = download_with_ytdlp(url, format_str, output_template)
    except RuntimeError as exc:
        log_error(str(exc))
        return EXIT_DOWNLOAD_ERROR
    except Exception as exc:
        log_error(f"Download failed: {exc}")
        return EXIT_DOWNLOAD_ERROR

    downloaded_path: Path = download_result["filepath"]

    if mode == "audio":
        mp3_path = downloaded_path.with_suffix(".mp3")
        try:
            convert_to_mp3(downloaded_path, mp3_path, bitrate=DEFAULT_AUDIO_BITRATE)
        except FileNotFoundError as exc:
            log_error(str(exc))
            return EXIT_FFMPEG_ERROR
        except CalledProcessError as exc:
            log_error(f"ffmpeg error: {exc.stderr.decode(errors='ignore') if exc.stderr else exc}")
            return EXIT_FFMPEG_ERROR
        log_info(f"Saved audio to: {mp3_path}")
    else:
        final_video_path = downloaded_path
        try:
            converted_path = convert_to_mp4_in_place(downloaded_path)
        except FileNotFoundError as exc:
            log_error(str(exc))
            return EXIT_FFMPEG_ERROR
        if converted_path:
            final_video_path = converted_path
            log_info(f"Downloaded and converted to: {final_video_path}")
        else:
            log_error("Conversion to mp4 failed; keeping original file (may be Resolve-incompatible).")
            log_info(f"Saved video to: {final_video_path}")

    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ripped CLI."""
    args = argv if argv is not None else sys.argv[1:]

    # No args or explicit "menu" enters interactive mode.
    if len(args) == 0 or (len(args) == 1 and args[0].lower() == "menu"):
        return run_menu()

    try:
        parsed: ParsedArgs = parse_args(args)
    except ValueError as exc:
        log_error(str(exc))
        return EXIT_USER_ERROR

    if parsed.mode == "convert":
        if parsed.path is None:
            log_error("A target path is required for convert mode.")
            return EXIT_USER_ERROR
        return run_bulk_conversion(parsed.path)

    if parsed.url is None:
        log_error("A URL is required for download modes.")
        return EXIT_USER_ERROR

    return perform_download(parsed.mode, parsed.quality, parsed.url)


def run_menu() -> int:
    """Interactive terminal menu for simplified usage."""
    mode = "video"
    quality: int | None = None
    _sentinel = object()
    status_message = "Ready"
    status_progress: float | None = None
    last_feedback = "Awaiting command."
    log_lines: list[str] = []

    def push_log(level: str, message: str | object) -> None:
        entry = f"[{level}] {message}"
        log_lines.append(entry)
        if len(log_lines) > 8:
            log_lines.pop(0)

    set_log_sink(push_log)

    def clear_screen() -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def _border() -> str:
        return FRAME_EDGE + (FRAME_FILL * (FRAME_WIDTH - 2)) + FRAME_EDGE

    def _row(text: str) -> str:
        inner = text[: FRAME_WIDTH - 4]
        return f"{FRAME_EDGE} {inner.ljust(FRAME_WIDTH - 4)} {FRAME_EDGE}"

    def _row_center(text: str) -> str:
        inner = text[: FRAME_WIDTH - 4]
        return f"{FRAME_EDGE} {inner.center(FRAME_WIDTH - 4)} {FRAME_EDGE}"

    def _progress(label: str, ratio: float = 0.0) -> str:
        ratio = max(0.0, min(1.0, ratio))
        bar_width = max(FRAME_WIDTH - len(label) - 12, 10)
        filled = int(bar_width * ratio)
        empty = max(bar_width - filled, 0)
        bar = (FRAME_EDGE * filled) + (FRAME_FILL * empty)
        text = f"{label}: [{bar}] {int(ratio*100):3d}%"
        return _row(text)

    def banner() -> None:
        clear_screen()
        print(MENU_ART)
        print(_border())
        print(_row_center("RIPPED CONTROL DECK"))
        print(_row(f"Mode: {mode:<8} | Quality: {format_quality_label(quality)}"))
        print(_row(f"Status: {status_message}"))
        if status_progress is not None:
            print(_progress("Activity", status_progress))
        print(_border())

    try:
        while True:
            banner()
            print(_row_center("MAIN MENU"))
            print(_row("1) Download single URL"))
            print(_row("2) Bulk download (enter URLs, 'q' to finish)"))
            print(_row("3) Convert existing videos to MP4"))
            print(_row("4) Change mode"))
            print(_row("5) Change quality"))
            print(_row("6) Exit"))
            print(_border())
            print(_row_center("LAST ACTION"))
            for line in last_feedback.splitlines() or [""]:
                print(_row(line))
            print(_border())
            print(_row_center("SESSION LOG"))
            if log_lines:
                for line in log_lines:
                    print(_row(line))
            else:
                print(_row("No log messages yet."))
            print(_border())
            print(_row_center("SELECT OPTION"))
            print(_border())

            choice = input("> ").strip()

            if choice == "1":
                url = prompt_for_url()
                if not url:
                    print("No URL provided.")
                    continue
                status_message = "Downloading..."
                status_progress = 0.0
                exit_code = perform_download(mode, quality, url)
                if exit_code != EXIT_OK:
                    print(f"Download finished with exit code {exit_code}")
                    last_feedback = f"Download finished with exit code {exit_code}"
                else:
                    last_feedback = f"Download complete\nURL: {url}"
                status_message = "Ready"
                status_progress = None
            elif choice == "2":
                urls = prompt_bulk_urls()
                if not urls:
                    print("No URLs provided.")
                    continue
                print(f"\nQueued {len(urls)} URLs. Starting downloads...")
                for idx, url in enumerate(urls, start=1):
                    print(f"[{idx}/{len(urls)}] {url}")
                    status_message = f"Downloading {idx}/{len(urls)}..."
                    status_progress = idx / len(urls)
                    exit_code = perform_download(mode, quality, url)
                    if exit_code != EXIT_OK:
                        print(f"  -> Failed with exit code {exit_code}")
                print("Bulk download complete.")
                last_feedback = f"Bulk download complete ({len(urls)} items)."
                status_message = "Ready"
                status_progress = None
            elif choice == "3":
                target = input("Enter file or directory to convert: ").strip()
                if not target:
                    print("No path provided.")
                    continue
                if not Path(target).expanduser().resolve().exists():
                    print("Path does not exist.")
                    continue
                status_message = "Converting..."
                status_progress = 0.0
                exit_code = run_bulk_conversion(target)
                if exit_code != EXIT_OK:
                    print(f"Conversion finished with exit code {exit_code}")
                    last_feedback = f"Conversion finished with exit code {exit_code}"
                else:
                    last_feedback = f"Conversion complete\nPath: {target}"
                status_message = "Ready"
                status_progress = None
            elif choice == "4":
                selected = prompt_mode()
                if selected:
                    mode = selected
                    last_feedback = f"Mode set to {mode}"
            elif choice == "5":
                selected_quality = prompt_quality(_sentinel)
                if selected_quality is not _sentinel:
                    quality = selected_quality
                    last_feedback = f"Quality set to {format_quality_label(quality)}"
            elif choice == "6":
                print("Goodbye.")
                return EXIT_OK
            else:
                print("Invalid choice. Please select 1-6.")
                last_feedback = "Invalid choice."
    finally:
        clear_log_sink()


def prompt_for_url() -> str | None:
    clip = read_clipboard()
    if clip:
        print(f"(Clipboard detected: {clip})")
    url = input("Enter URL (press Enter to use clipboard, or type/paste): ").strip()
    if not url and clip:
        url = clip
    if not url:
        return None
    try:
        return validate_url(url)
    except ValueError as exc:
        print(exc)
        return None


def prompt_bulk_urls() -> list[str]:
    # Windows: offer clipboard auto-capture without pressing Enter.
    if os.name == "nt" and msvcrt:
        if pyperclip is None:
            print("pyperclip is required for clipboard capture. Falling back to manual entry.")
            return _prompt_bulk_urls_fallback()
        # Capture baseline clipboard so we only react to new copies.
        baseline = read_clipboard()
        return _prompt_bulk_urls_windows(baseline_clip=baseline)

    return _prompt_bulk_urls_fallback()


def _prompt_bulk_urls_windows(baseline_clip: str | None) -> list[str]:
    """Windows-only loop that auto-adds URLs when clipboard changes."""
    print("Copy URLs (Ctrl+C) to queue automatically. Press 'q' to start downloads.")
    print("You can still type/paste a URL and press Enter to add manually.")
    print("Listening for clipboard changes...")
    urls: list[str] = []
    # Ignore whatever was on the clipboard when we entered bulk mode; react only to changes.
    last_clip: str | None = baseline_clip
    buffer: str = ""

    while True:
        # Clipboard capture
        clip = read_clipboard()
        if clip and clip != last_clip:
            try:
                validated = validate_url(clip)
                urls.append(validated)
                print(f"\n[+] Added from clipboard: {validated} (total {len(urls)})")
            except ValueError:
                # Ignore non-URL clipboard content
                pass
            last_clip = clip

        # Keyboard non-blocking read
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch.lower() == "q":
                print("\nStarting downloads...")
                break
            if ch in ("\r", "\n"):
                entry = buffer.strip()
                buffer = ""
                if not entry:
                    continue
                try:
                    validated = validate_url(entry)
                    urls.append(validated)
                    print(f"\n[+] Added: {validated} (total {len(urls)})")
                except ValueError as exc:
                    print(f"\n{exc}")
            elif ch == "\x08":  # backspace
                if buffer:
                    buffer = buffer[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            else:
                buffer += ch
                sys.stdout.write(ch)
                sys.stdout.flush()

        time.sleep(0.05)

    return urls


def _prompt_bulk_urls_fallback() -> list[str]:
    """Cross-platform manual entry with clipboard assist on Enter."""
    print("Enter URLs one per line. Type 'q' alone to start queueing downloads.")
    print("Press Enter with a copied URL to auto-use clipboard if detected.")
    urls: list[str] = []
    while True:
        clip = read_clipboard()
        if clip:
            print(f"(Clipboard: {clip})")
        entry = input("> ").strip()
        if entry.lower() == "q":
            break
        if not entry and clip:
            entry = clip
        if not entry:
            print("No URL entered.")
            continue
        try:
            validated = validate_url(entry)
            urls.append(validated)
        except ValueError as exc:
            print(exc)
    return urls


def prompt_mode() -> str | None:
    print("\nSelect mode:")
    print(" 1) audio")
    print(" 2) video")
    choice = input("Choice: ").strip()
    mapping = {"1": "audio", "2": "video"}
    if choice not in mapping:
        print("Invalid choice.")
        return None
    return mapping[choice]


def prompt_quality(invalid_sentinel: object) -> int | None | object:
    print("\nSelect quality:")
    for idx, q in enumerate(QUALITY_CHOICES, start=1):
        label = "max" if q is None else str(q)
        print(f" {idx}) {label}")
    choice = input("Choice: ").strip()
    try:
        choice_int = int(choice)
    except ValueError:
        print("Invalid choice.")
        return invalid_sentinel
    if not (1 <= choice_int <= len(QUALITY_CHOICES)):
        print("Invalid choice.")
        return invalid_sentinel
    return QUALITY_CHOICES[choice_int - 1]


if __name__ == "__main__":
    sys.exit(main())
