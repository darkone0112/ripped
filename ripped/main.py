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
from ripped.core.downloader import build_format_string, download_with_ytdlp
from ripped.core.ffmpeg_tools import convert_to_mp3
from ripped.utils.logger import log_error, log_info


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
        log_info(f"Saved video to: {downloaded_path}")

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

    return perform_download(parsed.mode, parsed.quality, parsed.url)


def run_menu() -> int:
    """Interactive terminal menu for simplified usage."""
    mode = "video"
    quality: int | None = None
    _sentinel = object()

    def banner() -> None:
        print("\n================ R I P P E D ================")
        print(f" Mode: {mode:<8} | Quality: {format_quality_label(quality)}")

    while True:
        banner()
        print("1) Download single URL")
        print("2) Bulk download (enter URLs, 'q' to finish)")
        print("3) Change mode")
        print("4) Change quality")
        print("5) Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            url = prompt_for_url()
            if not url:
                print("No URL provided.")
                continue
            exit_code = perform_download(mode, quality, url)
            if exit_code != EXIT_OK:
                print(f"Download finished with exit code {exit_code}")
        elif choice == "2":
            urls = prompt_bulk_urls()
            if not urls:
                print("No URLs provided.")
                continue
            print(f"\nQueued {len(urls)} URLs. Starting downloads...")
            for idx, url in enumerate(urls, start=1):
                print(f"[{idx}/{len(urls)}] {url}")
                exit_code = perform_download(mode, quality, url)
                if exit_code != EXIT_OK:
                    print(f"  -> Failed with exit code {exit_code}")
            print("Bulk download complete.")
        elif choice == "3":
            selected = prompt_mode()
            if selected:
                mode = selected
        elif choice == "4":
            selected_quality = prompt_quality(_sentinel)
            if selected_quality is not _sentinel:
                quality = selected_quality
        elif choice == "5":
            print("Goodbye.")
            return EXIT_OK
        else:
            print("Invalid choice. Please select 1-5.")


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
