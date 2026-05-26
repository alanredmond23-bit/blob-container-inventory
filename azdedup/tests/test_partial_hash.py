import xxhash

from azdedup.pipeline.partial_hash import (
    partial_hash_from_ranges,
    partial_hash_head_tail,
)


def test_partial_hash_head_tail_concatenates() -> None:
    head = b"alpha"
    tail = b"omega"
    expected = xxhash.xxh64(head + tail).hexdigest()
    assert partial_hash_head_tail(head, tail) == expected
    assert len(partial_hash_head_tail(head, tail)) == 16


def test_small_blob_hashes_head_only() -> None:
    blob = b"small blob content"
    read_bytes = 1024
    total_size = len(blob)

    result = partial_hash_from_ranges(blob, b"", total_size, read_bytes)
    expected = xxhash.xxh64(blob).hexdigest()

    assert total_size <= 2 * read_bytes
    assert result == expected
    assert result != partial_hash_head_tail(blob, blob)


def test_large_blob_hashes_head_and_tail() -> None:
    read_bytes = 8
    total_size = 32
    head = b"A" * read_bytes
    tail = b"Z" * read_bytes
    middle = b"M" * (total_size - 2 * read_bytes)
    full_blob = head + middle + tail

    result = partial_hash_from_ranges(head, tail, total_size, read_bytes)
    expected = partial_hash_head_tail(head, tail)

    assert total_size > 2 * read_bytes
    assert result == expected
    assert result != xxhash.xxh64(full_blob).hexdigest()
