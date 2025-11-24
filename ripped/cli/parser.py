from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedArgs:
    mode: str
    quality: Optional[int]
    url: str


def _validate_mode(raw_mode: str) -> str:
    mode = raw_mode.lower()
    if mode not in {"audio", "video"}:
        raise ValueError('Mode must be "audio" or "video".')
    return mode


def _validate_quality(raw_quality: str) -> Optional[int]:
    if raw_quality.lower() == "max":
        return None
    try:
        quality_int = int(raw_quality)
    except ValueError as exc:
        raise ValueError('Quality must be "max" or a positive integer.') from exc
    if quality_int <= 0:
        raise ValueError("Quality must be a positive integer.")
    return quality_int


def _validate_url(url: str) -> str:
    if not url.startswith("http"):
        raise ValueError("URL must start with http or https.")
    return url


def parse_args(argv: list[str]) -> ParsedArgs:
    """
    Parse minimal CLI arguments.

    Expected layout: ripped <mode> <quality> <url>
    """
    if len(argv) != 3:
        raise ValueError("Usage: ripped <mode> <quality> <url>")

    mode = _validate_mode(argv[0])
    quality = _validate_quality(argv[1])
    url = _validate_url(argv[2])

    return ParsedArgs(mode=mode, quality=quality, url=url)

