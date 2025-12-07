"""Local file storage for meetings data (JSON files and audio)."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .config import get_settings
from .logging_utils import get_logger

logger = get_logger(__name__)


class LocalStorage:
    """Stores meeting data locally in JSON files and audio files."""
    
    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.data_dir / "audio").mkdir(exist_ok=True)
        (self.data_dir / "events").mkdir(exist_ok=True)
        (self.data_dir / "sessions").mkdir(exist_ok=True)
        
        logger.info(
            "Local storage initialized",
            extra={"extra_data": {"data_dir": str(self.data_dir)}},
        )
    
    def save_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Save event to JSON file."""
        timestamp = datetime.now(timezone.utc)
        event_file = self.data_dir / "events" / f"{timestamp.strftime('%Y%m%d')}.jsonl"
        
        event_data = {
            "timestamp": timestamp.isoformat(),
            "event_type": event_type,
            "payload": payload,
        }
        
        with open(event_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_data, ensure_ascii=False) + "\n")
    
    def save_audio_file(self, meeting_id: str, session_id: str, chunk_id: str, audio_bytes: bytes) -> str:
        """Save audio file locally and return the file path."""
        audio_dir = self.data_dir / "audio" / meeting_id / session_id
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = audio_dir / f"{chunk_id}.wav"
        with open(file_path, "wb") as f:
            f.write(audio_bytes)
        
        return str(file_path.relative_to(self.data_dir))
    
    def save_session_data(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """Save session data to JSON file."""
        session_file = self.data_dir / "sessions" / f"{session_id}.json"
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False, default=str)
    
    def get_all_events(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all events from today's file."""
        today = datetime.now(timezone.utc).strftime('%Y%m%d')
        event_file = self.data_dir / "events" / f"{today}.jsonl"
        
        events = []
        if event_file.exists():
            with open(event_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        
        return events[-limit:] if limit else events
    
    def get_session_data(self, session_id: str) -> Dict[str, Any] | None:
        """Get session data from JSON file."""
        session_file = self.data_dir / "sessions" / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None


# Global instance
_local_storage: LocalStorage | None = None


def get_local_storage() -> LocalStorage:
    """Get or create global LocalStorage instance."""
    global _local_storage
    if _local_storage is None:
        settings = get_settings()
        _local_storage = LocalStorage(data_dir=settings.data_dir)
    return _local_storage






