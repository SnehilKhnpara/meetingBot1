from datetime import datetime
from enum import Enum
from typing import Optional
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










