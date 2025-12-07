from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

from azure.eventgrid import EventGridPublisherClient, EventGridEvent
from azure.core.credentials import AzureKeyCredential

from .config import get_settings
from .local_storage import get_local_storage
from .logging_utils import get_logger


logger = get_logger(__name__)


@dataclass
class EventPublisher:
    """Hybrid event publisher: saves locally by default, optionally publishes to Azure Event Grid."""

    client: EventGridPublisherClient | None

    @classmethod
    def create(cls) -> "EventPublisher":
        settings = get_settings()
        if not settings.azure_eventgrid_endpoint or not settings.azure_eventgrid_key:
            logger.info(
                "EventGrid not configured, events will be saved locally only",
                extra={"extra_data": {"component": "event_publisher", "mode": "local_only"}},
            )
            return cls(client=None)
        credential = AzureKeyCredential(settings.azure_eventgrid_key)
        client = EventGridPublisherClient(settings.azure_eventgrid_endpoint, credential)
        logger.info(
            "EventGrid configured, events will be saved to both local and Azure",
            extra={"extra_data": {"component": "event_publisher", "mode": "hybrid"}},
        )
        return cls(client=client)

    async def publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        logger.info(
            "Publishing event",
            extra={
                "extra_data": {
                    "event_type": event_type,
                    "payload": payload,
                    "timestamp": timestamp,
                }
            },
        )

        # Always save locally first
        local_storage = get_local_storage()
        local_storage.save_event(event_type, payload)

        # Optionally publish to Azure if configured
        if not self.client:
            return

        try:
            event = EventGridEvent(
                event_type=event_type,
                data=payload,
                subject=payload.get("meeting_id", "meeting"),
                data_version="1.0",
            )
            # EventGrid client is sync; use threadpool if needed.
            self.client.send([event])
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to publish event to Azure (local copy saved)",
                extra={
                    "extra_data": {
                        "event_type": event_type,
                        "error": str(exc),
                    }
                },
            )


event_publisher = EventPublisher.create()





