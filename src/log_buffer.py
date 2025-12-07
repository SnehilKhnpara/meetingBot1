"""In-memory log buffer for dashboard display."""
import json
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class LogBuffer:
    """Circular buffer storing recent log entries for dashboard."""

    def __init__(self, max_size: int = 1000) -> None:
        self._buffer: deque[Dict[str, Any]] = deque(maxlen=max_size)
        self._listeners: List[Any] = []  # For future SSE/WebSocket support

    def add(self, log_entry: Dict[str, Any]) -> None:
        """Add a log entry to the buffer."""
        self._buffer.append(log_entry)
        # Notify listeners (future SSE support)

    def get_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all logs, optionally limited to last N entries."""
        logs = list(self._buffer)
        if limit:
            return logs[-limit:]
        return logs

    def get_filtered(
        self,
        meeting_id: Optional[str] = None,
        session_id: Optional[str] = None,
        level: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get filtered logs."""
        logs = list(self._buffer)
        if meeting_id:
            logs = [l for l in logs if l.get("meeting_id") == meeting_id]
        if session_id:
            logs = [l for l in logs if l.get("session_id") == session_id]
        if level:
            logs = [l for l in logs if l.get("level", "").upper() == level.upper()]
        if limit:
            logs = logs[-limit:]
        return logs

    def clear(self) -> None:
        """Clear all logs."""
        self._buffer.clear()


# Global singleton
log_buffer = LogBuffer(max_size=2000)






