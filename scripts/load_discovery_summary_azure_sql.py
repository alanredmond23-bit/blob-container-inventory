#!/usr/bin/env python3
"""Deploy discovery_summary tables and load rows into Azure SQL."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "artifacts/catalog/discovery_summary_data.json"
SCHEMA = ROOT / "schema/discovery_summary.sql"


def connect():
    import pymssql

    host = os.environ["AZURE_SQL_HOST"]
    if not host.endswith(".database.windows.net"):
        host = host + ".database.windows.net"
    db = os.environ.get("AZURE_SQL_DB_NAME") or os.environ.get("AZURE_SQL_DB")
    return pymssql.connect(
        server=host,
        user=os.environ["AZURE_SQL_USER"],
        password=os.environ["AZURE_SQL_PASSWORD"],
        database=db,
        login_timeout=60,
    )


def run_ddl(cur) -> None:
    ddl = SCHEMA.read_text(encoding="utf-8")
    batches = [b.strip() for b in ddl.split("GO") if b.strip()]
    for batch in batches:
        cur.execute(batch)


def main() -> int:
    if not DATA.exists():
        print(f"Missing {DATA}", file=sys.stderr)
        return 1
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    rows = payload["rows"]
    photos = payload.get("photos", [])

    try:
        conn = connect()
    except Exception as e:
        print(f"Azure SQL connect failed: {e}", file=sys.stderr)
        print("Add firewall rule for this agent IP, then re-run.", file=sys.stderr)
        return 1

    cur = conn.cursor()
    run_ddl(cur)
    conn.commit()

    cur.execute("DELETE FROM dbo.discovery_summary_photos")
    cur.execute("DELETE FROM dbo.discovery_summary")
    conn.commit()

    ins = """
    INSERT INTO dbo.discovery_summary (
      source_page, sort_order, case_number, superseding_indictment_date, discovery_due_date,
      category, description, bates_begin, bates_end, doc_date, notes
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    case = payload["case_number"]
    si = payload["superseding_indictment_date"]
    dd = payload["discovery_due_date"]
    for r in rows:
        cur.execute(
            ins,
            (
                r["source_page"],
                r["sort_order"],
                case,
                si,
                dd,
                r["category"],
                r["description"],
                r.get("bates_begin"),
                r.get("bates_end"),
                r.get("doc_date"),
                r.get("notes"),
            ),
        )

    pins = """
    INSERT INTO dbo.discovery_summary_photos (photo_key, file_name, repo_path, md5_hash, is_duplicate, notes)
    VALUES (%s,%s,%s,%s,%s,%s)
    """
    for p in photos:
        cur.execute(
            pins,
            (
                p["photo_key"],
                p["file_name"],
                p["repo_path"],
                p.get("md5_hash"),
                1 if p.get("is_duplicate") else 0,
                p.get("notes"),
            ),
        )

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM dbo.discovery_summary")
    n = cur.fetchone()[0]
    print(f"Loaded {n} rows into dbo.discovery_summary")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
