#!/usr/bin/env python3
"""Unit test for inventory dedup analyzer."""
import csv
import tempfile
from pathlib import Path

from blob_dedup_from_inventory import analyze, CERTAINTY_PROVEN


def test_proven_exact_group():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "inv.csv"
        with p.open("w", newline="") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["Name", "Content-Length", "Content-MD5", "BlobType", "Last-Modified"],
            )
            w.writeheader()
            md5_b64 = "1B2M2Y8AsgTpgAmY7PhCfg=="  # empty file md5 example
            w.writerow(
                {
                    "Name": "container-a/file.bin",
                    "Content-Length": "100",
                    "Content-MD5": md5_b64,
                    "BlobType": "BlockBlob",
                    "Last-Modified": "2026-01-01",
                }
            )
            w.writerow(
                {
                    "Name": "container-b/file.bin",
                    "Content-Length": "100",
                    "Content-MD5": md5_b64,
                    "BlobType": "BlockBlob",
                    "Last-Modified": "2026-01-02",
                }
            )

        rows = __import__("blob_dedup_from_inventory").load_inventory(p)
        result = analyze(rows)
        assert result["stats"]["proven_groups"] == 1
        assert result["stats"]["delete_candidates"] == 1
        assert result["delete_candidates"][0]["certainty"] == CERTAINTY_PROVEN
        print("OK test_proven_exact_group")


if __name__ == "__main__":
    test_proven_exact_group()
