import os
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings, Settings
from .logging_utils import get_logger, setup_logging
from .log_buffer import log_buffer
from .cookie_manager import get_cookie_manager
from .models import ErrorResponse, JoinMeetingRequest, JoinMeetingResponse
from .session_manager import session_manager


setup_logging()
logger = get_logger(__name__)

app = FastAPI(title="Meeting Bot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


async def get_app_settings() -> Settings:
    return get_settings()


@app.on_event("startup")
async def on_startup() -> None:
    await session_manager.start()
    logger.info("API startup complete", extra={"extra_data": {"event": "startup"}})


@app.post(
    "/join-meeting",
    response_model=JoinMeetingResponse,
    responses={400: {"model": ErrorResponse}},
)
async def join_meeting(
    payload: JoinMeetingRequest,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> JoinMeetingResponse:
    try:
        session = await session_manager.enqueue_session(
            meeting_id=payload.meeting_id,
            platform=payload.platform,
            meeting_url=str(payload.meeting_url),
        )
    except ValueError as ve:
        logger.warning(
            "Join request rejected",
            extra={
                "extra_data": {
                    "event": "join_rejected",
                    "reason": str(ve),
                    "meeting_id": payload.meeting_id,
                    "platform": payload.platform.value,
                }
            },
        )
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(error=str(ve), code="INVALID_MEETING_URL").model_dump(),
        ) from ve
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Unexpected error in join_meeting",
            extra={
                "extra_data": {
                    "event": "join_error",
                    "meeting_id": payload.meeting_id,
                    "platform": payload.platform.value,
                    "error": str(exc),
                }
            },
        )
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to create meeting session", code="INTERNAL_ERROR"
            ).model_dump(),
        ) from exc

    logger.info(
        "Join request accepted",
        extra={
            "extra_data": {
                "event": "join_accepted",
                "meeting_id": payload.meeting_id,
                "platform": payload.platform.value,
                "session_id": session.session_id,
            }
        },
    )
    return JoinMeetingResponse(session_id=session.session_id)


@app.get("/healthz")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/")
async def root() -> FileResponse:
    """Serve the dashboard UI."""
    dashboard_path = static_dir / "index.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    return JSONResponse({"message": "Dashboard not found"})


@app.get("/sessions")
async def list_sessions() -> JSONResponse:
    """List all sessions for dashboard."""
    items = []
    # shallow import here to avoid cycle
    from .session_manager import session_manager as sm  # type: ignore

    for s in sm._sessions.values():  # noqa: SLF001
        items.append(
            {
                "meeting_id": s.meeting_id,
                "platform": s.platform.value,
                "session_id": s.session_id,
                "status": s.status.value,
                "created_at": s.created_at.isoformat(),
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            }
        )
    return JSONResponse(items)


@app.get("/logs")
async def get_logs(
    limit: int = 500,
    meeting_id: str | None = None,
    session_id: str | None = None,
    level: str | None = None,
) -> JSONResponse:
    """Get logs for dashboard."""
    if meeting_id or session_id or level:
        logs = log_buffer.get_filtered(
            meeting_id=meeting_id,
            session_id=session_id,
            level=level,
            limit=limit,
        )
    else:
        logs = log_buffer.get_all(limit=limit)
    return JSONResponse(logs)


@app.post("/logs/clear")
async def clear_logs() -> JSONResponse:
    """Clear all logs."""
    log_buffer.clear()
    logger.info("Logs cleared", extra={"extra_data": {"event": "logs_cleared"}})
    return JSONResponse({"status": "cleared"})


@app.get("/cookies/status")
async def get_cookie_status(platform: str = "gmeet") -> JSONResponse:
    """Get cookie authentication status."""
    cookie_manager = get_cookie_manager()
    status = cookie_manager.get_cookie_status(platform)
    return JSONResponse(status)
