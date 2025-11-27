import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List

from ripped.config.settings import DEFAULT_AUDIO_BITRATE
from ripped.utils.logger import log_error, log_info


MEDIA_EXTENSIONS = {".webm", ".mkv"}


def _require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise FileNotFoundError("ffmpeg not found. Please install ffmpeg and ensure it is in your PATH.")


def _normalize_path(target: Path | str) -> Path:
    return Path(target).expanduser().resolve()


def find_media_files(target_path: Path | str) -> List[Path]:
    """Return a list of .webm/.mkv files under the given path (recursive)."""
    root = _normalize_path(target_path)

    if root.is_file():
        return [root] if root.suffix.lower() in MEDIA_EXTENSIONS else []

    if not root.is_dir():
        return []

    matches: List[Path] = []
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            candidate = Path(dirpath) / filename
            if candidate.suffix.lower() in MEDIA_EXTENSIONS:
                matches.append(candidate.resolve())
    return matches


def _dedupe_output_path(base_output: Path) -> Path:
    output_path = base_output
    counter = 1
    while output_path.exists():
        output_path = output_path.with_name(f"{base_output.stem}_converted{'' if counter == 1 else f'_{counter-1}'}{base_output.suffix}")
        counter += 1
    return output_path


def _run_ffmpeg(cmd: Iterable[str]) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(cmd, check=False, capture_output=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError("ffmpeg not found. Please install ffmpeg and ensure it is in your PATH.") from exc


def convert_to_mp4_in_place(input_path: Path | str) -> Path | None:
    """
    Convert a single media file to mp4 (AAC audio) in-place.

    Returns the output path on success, or None on failure.
    """
    _require_ffmpeg()

    source = _normalize_path(input_path)
    suffix = source.suffix.lower()

    if not source.exists():
        log_error(f"Input file does not exist: {source}")
        return None

    if suffix == ".mp4":
        log_info(f"Already mp4, skipping conversion: {source}")
        return source
    if suffix not in MEDIA_EXTENSIONS:
        log_error(f"Unsupported file type for conversion: {source}")
        return None

    desired_output = source.with_suffix(".mp4")
    output_path = _dedupe_output_path(desired_output) if desired_output.exists() else desired_output

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        DEFAULT_AUDIO_BITRATE,
        str(output_path),
    ]

    log_info(f"Converting {source} to MP4")
    result = _run_ffmpeg(cmd)

    if result.returncode != 0:
        log_error(f"Conversion failed for {source}: {result.stderr.decode(errors='ignore') if result.stderr else 'unknown error'}")
        if output_path.exists():
            output_path.unlink(missing_ok=True)
        return None

    if not output_path.exists() or output_path.stat().st_size == 0:
        log_error(f"Conversion failed for {source}: output not created")
        if output_path.exists():
            output_path.unlink(missing_ok=True)
        return None

    try:
        source.unlink()
    except OSError as exc:
        log_error(f"Converted to {output_path} but could not delete original: {exc}")
        return output_path

    log_info(f"Successfully converted to {output_path}, deleting original")
    return output_path


def run_bulk_conversion(target_path: Path | str) -> int:
    """
    Convert all .webm/.mkv under the target path to .mp4.

    Returns exit code: 0 if at least one success, 2 otherwise.
    """
    root = _normalize_path(target_path)
    files = find_media_files(root)

    if not files:
        log_info("No webm/mkv files found in path")
        return 2

    try:
        _require_ffmpeg()
    except FileNotFoundError as exc:
        log_error(str(exc))
        return 2

    success_count = 0
    failure_count = 0

    try:
        for media_file in files:
            log_info(f"Converting: {media_file}")
            result = convert_to_mp4_in_place(media_file)
            if result:
                success_count += 1
            else:
                failure_count += 1
    except KeyboardInterrupt:
        log_info("Conversion interrupted by user; leaving existing files untouched.")

    processed = success_count + failure_count
    log_info(f"Processed {processed} files: {success_count} converted, {failure_count} failed")

    return 0 if success_count > 0 else 2
