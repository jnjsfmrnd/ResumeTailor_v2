from __future__ import annotations

import importlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from azure.storage.blob import BlobServiceClient
from django.conf import settings


@dataclass(slots=True)
class StoredBlob:
    path: str
    size: int


class DurableStorageBackend(ABC):
    @abstractmethod
    def save_bytes(self, blob_path: str, content: bytes, *, content_type: str) -> StoredBlob:
        raise NotImplementedError

    @abstractmethod
    def open_bytes(self, blob_path: str) -> bytes:
        raise NotImplementedError


class LocalFileStorageBackend(DurableStorageBackend):
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root or settings.MEDIA_ROOT)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, blob_path: str, content: bytes, *, content_type: str) -> StoredBlob:
        destination = self.root / blob_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return StoredBlob(path=blob_path, size=len(content))

    def open_bytes(self, blob_path: str) -> bytes:
        return (self.root / blob_path).read_bytes()


class AzureBlobStorageBackend(DurableStorageBackend):
    def __init__(self) -> None:
        account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
        account_key = settings.AZURE_STORAGE_ACCOUNT_KEY
        endpoint = getattr(settings, "AZURE_BLOB_ENDPOINT", f"https://{account_name}.blob.core.windows.net")
        if account_key:
            credential = account_key
        else:
            credential_module = importlib.import_module("azure.identity")
            credential = credential_module.DefaultAzureCredential(
                exclude_interactive_browser_credential=True
            )
        self.client = BlobServiceClient(account_url=endpoint, credential=credential)
        self.container_name = getattr(
            settings,
            "AZURE_STORAGE_CONTAINER_NAME",
            settings.AZURE_STORAGE_CONTAINER,
        )

    def save_bytes(self, blob_path: str, content: bytes, *, content_type: str) -> StoredBlob:
        blob_client = self.client.get_blob_client(container=self.container_name, blob=blob_path)
        blob_client.upload_blob(
            content,
            overwrite=True,
            content_type=content_type,
        )
        return StoredBlob(path=blob_path, size=len(content))

    def open_bytes(self, blob_path: str) -> bytes:
        blob_client = self.client.get_blob_client(container=self.container_name, blob=blob_path)
        return blob_client.download_blob().readall()