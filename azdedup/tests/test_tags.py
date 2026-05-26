from azdedup.tags import merge_tags


def test_merge_tags_overflow_drops_ext() -> None:
    base = {f"k{i}": "v" for i in range(9)}
    base["ext"] = "pdf"
    merged = merge_tags(base, {"dedup_stage": "meta", "size": "123"})
    assert "ext" not in merged or len(merged) <= 10
    assert merged["dedup_stage"] == "meta"
