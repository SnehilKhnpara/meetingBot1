import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "extra_data") and isinstance(
            record.extra_data, dict
        ):  # type: ignore[attr-defined]
            payload.update(record.extra_data)  # type: ignore[arg-type]
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        
        return json.dumps(payload, ensure_ascii=False)


class BufferHandler(logging.Handler):
    """Custom handler that also stores logs in buffer for dashboard."""
    
    def emit(self, record: logging.LogRecord) -> None:
        try:
            from .log_buffer import log_buffer  # Lazy import to avoid circular deps
            
            payload: Dict[str, Any] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name,
            }
            if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):  # type: ignore[attr-defined]
                payload.update(record.extra_data)  # type: ignore[arg-type]
            if record.exc_info:
                formatter = logging.Formatter()
                payload["exc_info"] = formatter.formatException(record.exc_info)
            
            log_buffer.add(payload)
        except Exception:  # noqa: BLE001
            pass  # Don't break logging if buffer fails


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    # Clear existing handlers (useful for reloads)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    
    # Also add buffer handler for dashboard
    buffer_handler = BufferHandler()
    buffer_handler.setLevel(level)
    root.addHandler(buffer_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name or "meeting-bot")





