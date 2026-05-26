"""Azure Blob Storage client helpers."""

from __future__ import annotations

import os

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


def get_blob_service_client(account: str) -> BlobServiceClient:
    """Return a BlobServiceClient using key, connection string, or DefaultAzureCredential."""
    conn = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if conn:
        return BlobServiceClient.from_connection_string(conn)

    key = os.environ.get("AZURE_STORAGE_KEY")
    if key:
        return BlobServiceClient(
            account_url=f"https://{account}.blob.core.windows.net",
            credential=key,
        )

    return BlobServiceClient(
        account_url=f"https://{account}.blob.core.windows.net",
        credential=DefaultAzureCredential(),
    )


def list_account_containers(client: BlobServiceClient) -> list[str]:
    """List all container names in the storage account."""
    return [container.name for container in client.list_containers()]


def get_blob_tags(client: BlobServiceClient, container: str, blob_path: str) -> dict[str, str]:
    """Return blob index tags, or {} when the blob is missing."""
    blob_client = client.get_blob_client(container=container, blob=blob_path)
    try:
        tags = blob_client.get_blob_tags()
    except ResourceNotFoundError:
        return {}
    return dict(tags or {})


def set_blob_tags(
    client: BlobServiceClient,
    container: str,
    blob_path: str,
    tags: dict[str, str],
) -> None:
    """Replace blob index tags."""
    blob_client = client.get_blob_client(container=container, blob=blob_path)
    blob_client.set_blob_tags(tags)
