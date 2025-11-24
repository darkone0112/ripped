import shutil
import subprocess
from pathlib import Path


def _require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise FileNotFoundError("ffmpeg not found in PATH. Please install ffmpeg to proceed.")


def convert_to_mp3(input_path: Path, output_path: Path, bitrate: str = "192k") -> Path:
    """Convert an audio file to mp3 using ffmpeg."""
    _require_ffmpeg()
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def merge_audio_video(video_path: Path, audio_path: Path, output_path: Path) -> Path:
    """Mux separate audio and video files into a single mp4."""
    _require_ffmpeg()
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

