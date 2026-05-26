from types import SimpleNamespace
from unittest.mock import MagicMock

from azure.core.exceptions import ResourceNotFoundError

from azdedup import azure_client


def test_get_blob_tags_missing_returns_empty() -> None:
    client = MagicMock()
    blob_client = MagicMock()
    client.get_blob_client.return_value = blob_client
    blob_client.get_blob_tags.side_effect = ResourceNotFoundError("missing")

    assert azure_client.get_blob_tags(client, "c1", "missing.txt") == {}


def test_get_blob_tags_returns_dict() -> None:
    client = MagicMock()
    blob_client = MagicMock()
    client.get_blob_client.return_value = blob_client
    blob_client.get_blob_tags.return_value = {"dedup_stage": "meta"}

    assert azure_client.get_blob_tags(client, "c1", "a.txt") == {"dedup_stage": "meta"}


def test_list_account_containers() -> None:
    client = MagicMock()
    client.list_containers.return_value = [
        SimpleNamespace(name="a"),
        SimpleNamespace(name="b"),
    ]
    assert azure_client.list_account_containers(client) == ["a", "b"]
