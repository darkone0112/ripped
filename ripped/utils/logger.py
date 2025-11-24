from datetime import datetime
from typing import Any


def _timestamp() -> str:
    return datetime.utcnow().strftime("%H:%M:%S")


def log_info(message: Any) -> None:
    print(f"[{_timestamp()}] INFO: {message}")


def log_error(message: Any) -> None:
    print(f"[{_timestamp()}] ERROR: {message}")


def log_debug(message: Any) -> None:
    print(f"[{_timestamp()}] DEBUG: {message}")

