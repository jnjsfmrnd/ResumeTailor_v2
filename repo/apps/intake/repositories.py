from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import transaction

from apps.common.models import WorkspaceSession
from apps.intake.models import SourceDocument
from apps.intake.storage import (
    AzureBlobStorageBackend,
    DurableStorageBackend,
    LocalFileStorageBackend,
)


def get_storage_backend() -> DurableStorageBackend:
    if settings.USE_LOCAL_FILE_STORAGE:
        return LocalFileStorageBackend()
    return AzureBlobStorageBackend()


@dataclass(slots=True)
class StoredSourceDocument:
    document: SourceDocument
    content: bytes


class SourceDocumentRepository:
    def __init__(self, storage_backend: DurableStorageBackend | None = None) -> None:
        self.storage_backend = storage_backend or get_storage_backend()

    @transaction.atomic
    def create_uploaded_document(
        self,
        *,
        workspace_session: WorkspaceSession,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> StoredSourceDocument:
        safe_name = Path(filename).name
        digest = hashlib.sha256(content).hexdigest()
        blob_path = f"uploads/{workspace_session.id}/{uuid4()}-{safe_name}"
        self.storage_backend.save_bytes(blob_path, content, content_type=content_type)

        workspace_session.source_documents.update(is_current=False)
        document = SourceDocument.objects.create(
            workspace_session=workspace_session,
            original_filename=safe_name,
            content_type=content_type,
            blob_path=blob_path,
            sha256=digest,
            is_current=True,
        )
        workspace_session.current_source_document = document
        workspace_session.save(update_fields=["current_source_document", "updated_at"])
        return StoredSourceDocument(document=document, content=content)

    def read_content(self, document: SourceDocument) -> bytes:
        return self.storage_backend.open_bytes(document.blob_path)