from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import httpx

from .config import get_settings
from .logging_utils import get_logger


logger = get_logger(__name__)


@dataclass
class SpeakerLabel:
    label: str
    confidence: float


async def _call_external_diarization_api(
    meeting_id: str,
    session_id: str,
    chunk_id: str,
    audio_bytes: bytes,
) -> List[SpeakerLabel]:
    settings = get_settings()
    if not settings.diarization_api_url:
        return []

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            files = {"audio": (f"{chunk_id}.wav", audio_bytes, "audio/wav")}
            data: Dict[str, Any] = {
                "meeting_id": meeting_id,
                "session_id": session_id,
                "chunk_id": chunk_id,
            }
            resp = await client.post(settings.diarization_api_url, data=data, files=files)
            resp.raise_for_status()
            payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Diarization API call failed",
            extra={
                "extra_data": {
                    "meeting_id": meeting_id,
                    "session_id": session_id,
                    "chunk_id": chunk_id,
                    "error": str(exc),
                }
            },
        )
        return []

    speakers: List[SpeakerLabel] = []
    for item in payload.get("speakers", []):
        label = str(item.get("label", "speaker_1"))
        confidence = float(item.get("confidence", 0.5))
        speakers.append(SpeakerLabel(label=label, confidence=confidence))
    return speakers


async def analyze_chunk(
    meeting_id: str,
    session_id: str,
    chunk_id: str,
    audio_bytes: bytes,
) -> List[SpeakerLabel]:
    """Return list of speaker labels for this chunk.

    If DIARIZATION_API_URL is configured, this will call that HTTP endpoint.
    Otherwise it falls back to a simple single-speaker stub.
    """
    settings = get_settings()
    if settings.diarization_api_url:
        speakers = await _call_external_diarization_api(
            meeting_id=meeting_id,
            session_id=session_id,
            chunk_id=chunk_id,
            audio_bytes=audio_bytes,
        )
        if speakers:
            return speakers

    # Fallback: single generic speaker label
    logger.info(
        "DEVELOPER: Using fallback diarization (single-speaker stub)",
        extra={
            "extra_data": {
                "meeting_id": meeting_id,
                "session_id": session_id,
                "chunk_id": chunk_id,
                "audio_size_bytes": len(audio_bytes),
                "diarization_method": "fallback",
            }
        },
    )
    return [SpeakerLabel(label="speaker_1", confidence=0.5)]









