"""Full (SHA-256) hashing and collision grouping for the dedup full stage."""

from __future__ import annotations

import base64
import hashlib
from collections import defaultdict
from typing import Any

from azure.storage.blob import BlobServiceClient


def normalize_inventory_md5(raw: str | None) -> str | None:
    """Normalize inventory Content-MD5 values to lowercase hex."""
    if raw is None or raw == "" or str(raw).lower() in ("none", "null"):
        return None
    s = str(raw).strip()
    if len(s) == 24 and s.endswith("=="):
        try:
            return base64.b64decode(s).hex()
        except Exception:
            pass
    if len(s) == 32 and all(c in "0123456789abcdefABCDEF" for c in s):
        return s.lower()
    try:
        return base64.b64decode(s).hex()
    except Exception:
        return None


def sha256_blob(client: BlobServiceClient, container: str, blob_path: str) -> str:
    """Stream SHA-256 over the full blob contents."""
    blob_client = client.get_blob_client(container=container, blob=blob_path)
    hasher = hashlib.sha256()
    download = blob_client.download_blob()
    for chunk in download.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()


def md5_shortcut_hash(md5_hex: str) -> str:
    """Return tag-safe hash when inventory MD5 proves an exact match."""
    return f"md5:{md5_hex}"


class CollisionGrouper:
    """Group blobs by (size, hash_fast) for full-stage collision resolution."""

    def __init__(self) -> None:
        self._groups: dict[tuple[int, str], list[Any]] = defaultdict(list)

    def add(self, blob_ref: Any, hash_fast: str) -> None:
        self._groups[(blob_ref.size, hash_fast)].append(blob_ref)

    def collision_groups(self) -> list[list[Any]]:
        return [members for members in self._groups.values() if len(members) >= 2]

    @property
    def total_entries(self) -> int:
        return sum(len(members) for members in self._groups.values())


def try_md5_group_hash(members: list[Any]) -> str | None:
    """Return md5 shortcut hash when every member shares the same non-empty MD5."""
    md5: str | None = None
    for member in members:
        content_md5 = getattr(member, "content_md5", None)
        if not content_md5:
            return None
        if md5 is None:
            md5 = content_md5
        elif content_md5 != md5:
            return None
    return md5_shortcut_hash(md5) if md5 else None


def resolve_full_hash(
    client: BlobServiceClient,
    blob: Any,
    *,
    content_md5: str | None = None,
) -> str:
    """Return hash_full using inventory MD5 shortcut when available, else SHA-256."""
    md5 = content_md5 or getattr(blob, "content_md5", None)
    if md5:
        return md5_shortcut_hash(md5)
    return sha256_blob(client, blob.container, blob.blob_path)
