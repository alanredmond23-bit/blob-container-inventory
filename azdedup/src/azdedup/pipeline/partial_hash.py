"""Partial (fast) hashing via xxhash64 over head/tail byte ranges."""

from __future__ import annotations

import xxhash
from azure.storage.blob import BlobServiceClient

from azdedup.azure_client import download_blob_bytes


def partial_hash_head_tail(head: bytes, tail: bytes) -> str:
    """Return xxhash64 hex digest of concatenated head and tail bytes."""
    hasher = xxhash.xxh64()
    hasher.update(head)
    hasher.update(tail)
    return hasher.hexdigest()


def partial_hash_from_ranges(
    head: bytes,
    tail: bytes,
    total_size: int,
    read_bytes: int,
) -> str:
    """Hash head/tail ranges; small blobs use a single hash of head only."""
    if total_size <= 2 * read_bytes:
        return xxhash.xxh64(head).hexdigest()
    return partial_hash_head_tail(head, tail)


def compute_partial_hash(
    client: BlobServiceClient,
    container: str,
    blob_path: str,
    size: int,
    read_bytes: int,
) -> str:
    """Download head/tail ranges from Azure and return the partial hash."""
    head_len = min(read_bytes, size)
    head = download_blob_bytes(client, container, blob_path, offset=0, length=head_len)

    if size <= 2 * read_bytes:
        return partial_hash_from_ranges(head, b"", size, read_bytes)

    tail = download_blob_bytes(
        client,
        container,
        blob_path,
        offset=size - read_bytes,
        length=read_bytes,
    )
    return partial_hash_from_ranges(head, tail, size, read_bytes)
