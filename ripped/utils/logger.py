from datetime import datetime
from typing import Any, Callable, Optional

LogSink = Callable[[str, Any], None]
_custom_sink: Optional[LogSink] = None


def _timestamp() -> str:
    return datetime.utcnow().strftime("%H:%M:%S")


def log_info(message: Any) -> None:
    if _custom_sink:
        _custom_sink("INFO", message)
    else:
        print(f"[{_timestamp()}] INFO: {message}")


def log_error(message: Any) -> None:
    if _custom_sink:
        _custom_sink("ERROR", message)
    else:
        print(f"[{_timestamp()}] ERROR: {message}")


def log_debug(message: Any) -> None:
    if _custom_sink:
        _custom_sink("DEBUG", message)
    else:
        print(f"[{_timestamp()}] DEBUG: {message}")


def set_log_sink(sink: LogSink | None) -> None:
    global _custom_sink
    _custom_sink = sink


def clear_log_sink() -> None:
    set_log_sink(None)
