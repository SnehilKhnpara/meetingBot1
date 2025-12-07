from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

from azure.storage.blob import BlobServiceClient

from .config import get_settings
from .local_storage import get_local_storage
from .logging_utils import get_logger


logger = get_logger(__name__)


@dataclass
class BlobStorageClient:
    """Hybrid storage: saves locally by default, optionally uploads to Azure."""
    service_client: Optional[BlobServiceClient]
    container_name: Optional[str]

    @classmethod
    def create(cls) -> "BlobStorageClient":
        settings = get_settings()
        if not settings.azure_blob_connection_string or not settings.azure_blob_container:
            logger.info(
                "Azure Blob Storage not configured, using local storage only",
                extra={"extra_data": {"component": "blob_storage", "mode": "local_only"}},
            )
            return cls(service_client=None, container_name=None)
        service_client = BlobServiceClient.from_connection_string(
            settings.azure_blob_connection_string
        )
        logger.info(
            "Azure Blob Storage configured, will save to both local and Azure",
            extra={"extra_data": {"component": "blob_storage", "mode": "hybrid"}},
        )
        return cls(service_client=service_client, container_name=settings.azure_blob_container)

    async def upload_bytes_with_retry(
        self,
        blob_path: str,
        data: bytes,
        content_type: str = "audio/wav",
        max_retries: int = 3,
    ) -> str:
        """Save audio locally and optionally upload to Azure. Returns local file path."""
        # Always save locally first
        local_storage = get_local_storage()
        
        # Extract meeting_id and session_id from blob_path (format: meeting_id/session_id/timestamp.wav)
        parts = blob_path.split("/")
        if len(parts) >= 3:
            meeting_id = parts[0]
            session_id = parts[1]
            chunk_id = parts[2].replace(".wav", "")
            local_path = local_storage.save_audio_file(meeting_id, session_id, chunk_id, data)
            logger.info(
                "Saved audio locally",
                extra={"extra_data": {"local_path": local_path, "blob_path": blob_path}},
            )
        else:
            # Fallback: save with full blob_path
            local_path = f"audio/{blob_path}"
            audio_file = local_storage.data_dir / local_path
            audio_file.parent.mkdir(parents=True, exist_ok=True)
            with open(audio_file, "wb") as f:
                f.write(data)
        
        # Optionally upload to Azure if configured
        if not self.service_client or not self.container_name:
            return local_path

        for attempt in range(1, max_retries + 1):
            try:
                container_client = self.service_client.get_container_client(self.container_name)
                blob_client = container_client.get_blob_client(blob_path)
                # azure-storage-blob is sync; run in thread pool
                await asyncio.to_thread(
                    blob_client.upload_blob,
                    data,
                    overwrite=True,
                    content_type=content_type,
                )
                logger.info(
                    "Uploaded blob to Azure",
                    extra={
                        "extra_data": {
                            "blob_path": blob_path,
                            "attempt": attempt,
                        }
                    },
                )
                break
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Azure blob upload failed (local copy saved)",
                    extra={
                        "extra_data": {
                            "blob_path": blob_path,
                            "attempt": attempt,
                            "error": str(exc),
                        }
                    },
                )
                if attempt == max_retries:
                    # Local copy is saved, so we don't raise
                    pass
                else:
                    await asyncio.sleep(2 * attempt)
        
        return local_path


blob_storage = BlobStorageClient.create()





