from azdedup.pipeline.incremental import needs_meta_scan, should_apply_meta
from azdedup.tags import meta_tags_for_blob


ETAG_A = "0x8DE9C48237CA441"
ETAG_B = "0x8DE9C48347376A8"


def test_new_blob_needs_meta_scan() -> None:
    assert needs_meta_scan(None, ETAG_A) is True
    apply, reason = should_apply_meta(None, ETAG_A)
    assert apply is True
    assert reason == "new_blob"


def test_etag_changed_needs_meta_scan() -> None:
    existing = meta_tags_for_blob(1024, "pdf", ETAG_A)
    assert needs_meta_scan(existing, ETAG_B) is True
    apply, reason = should_apply_meta(existing, ETAG_B)
    assert apply is True
    assert reason == "etag_changed"


def test_meta_same_etag_skips() -> None:
    existing = meta_tags_for_blob(1024, "pdf", ETAG_A)
    assert needs_meta_scan(existing, ETAG_A) is False
    apply, reason = should_apply_meta(existing, ETAG_A)
    assert apply is False
    assert reason == "skip"


def test_force_rescan_despite_up_to_date() -> None:
    existing = meta_tags_for_blob(1024, "pdf", ETAG_A)
    assert needs_meta_scan(existing, ETAG_A, force=True) is True
    apply, reason = should_apply_meta(existing, ETAG_A, force=True)
    assert apply is True
    assert reason == "force"
