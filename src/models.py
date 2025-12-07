from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, AnyHttpUrl, Field


class Platform(str, Enum):
    teams = "teams"
    gmeet = "gmeet"


class JoinMeetingRequest(BaseModel):
    meeting_id: str = Field(..., description="Internal meeting identifier")
    meeting_url: AnyHttpUrl = Field(..., description="Teams or Google Meet URL")
    platform: Platform
    start_time: Optional[datetime] = Field(
        None, description="Optional scheduled start time (UTC)"
    )


class JoinMeetingResponse(BaseModel):
    session_id: str
    status: str = "queued"


class ErrorResponse(BaseModel):
    error: str
    code: str


class SessionStatus(str, Enum):
    created = "created"
    joining = "joining"
    in_meeting = "in_meeting"
    ended = "ended"
    failed = "failed"


class ParticipantSnapshot(BaseModel):
    """Participant information at a specific point in time."""
    name: str
    original_name: Optional[str] = None
    is_bot: bool = False
    role: str = "guest"
    is_speaking: bool = False


class SpeakerInfo(BaseModel):
    """Speaker identification information."""
    speaker_label: str  # e.g., "speaker_1", "John Doe"
    speaker_name: Optional[str] = None  # Mapped participant name
    confidence: float
    is_bot: bool = False


class AudioChunkData(BaseModel):
    """
    Unified data model for 30-second audio chunks.

    Contains all information about what happened during this chunk:
    - Audio file location
    - Time boundaries
    - All participants present
    - Active speaker
    - Speaker events
    """
    # Identifiers
    chunk_id: str
    chunk_number: int
    meeting_id: str
    session_id: str

    # Time boundaries
    start_timestamp: datetime
    end_timestamp: datetime
    duration_seconds: float = 30.0

    # Audio file
    audio_file_path: str  # Local path to .wav file
    audio_file_size_bytes: int = 0
    audio_blob_path: Optional[str] = None  # Azure blob path (if used)

    # Participants during this chunk
    participants: List[ParticipantSnapshot] = Field(default_factory=list)
    participant_count: int = 0
    real_participant_count: int = 0  # Excludes bot

    # Active speaker
    active_speaker: Optional[SpeakerInfo] = None
    all_speakers: List[SpeakerInfo] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now())

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with datetime serialization."""
        data = self.dict()
        # Ensure datetimes are ISO format
        for key in ['start_timestamp', 'end_timestamp', 'created_at']:
            if key in data and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        return data

    def generate_filename(self) -> str:
        """
        Generate predictable filename: chunk_001_bot_user1_2025-02-15T10-20-00.wav
        """
        # Format chunk number with leading zeros
        chunk_num_str = f"{self.chunk_number:03d}"

        # Get participant names (excluding bot)
        participant_names = []
        bot_name = None

        for p in self.participants:
            if p.is_bot:
                bot_name = p.name.lower().replace(" ", "")
            else:
                # Take first 10 chars of name, remove spaces
                clean_name = p.name[:10].replace(" ", "").lower()
                if clean_name and clean_name not in participant_names:
                    participant_names.append(clean_name)

        # Build filename components
        components = [f"chunk_{chunk_num_str}"]

        if bot_name:
            components.append(bot_name)

        # Add up to 3 participant names
        if participant_names:
            components.extend(participant_names[:3])

        # Add timestamp (safe for filenames)
        timestamp_safe = self.start_timestamp.isoformat().replace(":", "-").split(".")[0]
        components.append(timestamp_safe)

        return "_".join(components) + ".wav"










