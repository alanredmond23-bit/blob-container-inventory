#!/usr/bin/env python3
"""Read latest Kanban export; emit delete queue + export state for the agent."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def card_info(card_id: str, cards: dict) -> dict:
    c = cards.get(card_id) or {}
    return {
        "id": card_id,
        "label": c.get("label", card_id),
        "container": c.get("container"),
        "folder": c.get("folder"),
        "blobs": c.get("blobs"),
        "bytes": c.get("bytes"),
        "bytes_human": c.get("bytes_human"),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    homes = root / "artifacts/catalog/blob_homes_assignments.json"
    kanban = root / "artifacts/catalog/kanban_data.json"
    state_path = root / "artifacts/catalog/HOMES_EXPORT_STATE.json"
    delete_manifest = root / "artifacts/catalog/DELETE_QUEUE_MANIFEST.json"

    if not homes.exists():
        print(f"Missing {homes}", file=sys.stderr)
        return 1

    data = json.loads(homes.read_text(encoding="utf-8"))
    assignments = data.get("assignments") or {}
    exported_at = data.get("exported_at") or data.get("updated_at")

    cards: dict = {}
    if kanban.exists():
        cards = {c["id"]: c for c in json.loads(kanban.read_text())["cards"]}

    delete_queue: list[dict] = []
    by_zone: dict[str, list] = {}
    for cid, entry in assignments.items():
        path = entry.get("path") or []
        if not path:
            continue
        zone = " → ".join(path)
        by_zone.setdefault(zone, []).append(card_info(cid, cards))
        if path[:2] == ["delete-queue", "approved"]:
            delete_queue.append({**card_info(cid, cards), "path": path, "moved_at": entry.get("moved_at")})

    state = {
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "exported_at": exported_at,
        "assignment_count": len(assignments),
        "delete_queue_count": len(delete_queue),
        "zones": {k: len(v) for k, v in sorted(by_zone.items(), key=lambda x: -len(x[1]))[:30]},
    }
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    delete_manifest.write_text(
        json.dumps(
            {
                "exported_at": exported_at,
                "ready_for_execution": len(delete_queue) > 0,
                "items": delete_queue,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(state, indent=2))
    if delete_queue:
        print(f"\nDELETE QUEUE: {len(delete_queue)} items — see {delete_manifest}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
