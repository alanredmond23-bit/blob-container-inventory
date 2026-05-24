#!/usr/bin/env python3
"""Find same-size and similar-name folder groups in Kanban zone inboxes."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path


def norm_name(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def leaf_name(label: str) -> str:
    if " / " in label:
        return label.split(" / ")[-1]
    return label


def similar(a: str, b: str) -> bool:
    la, lb = leaf_name(a), leaf_name(b)
    na, nb = norm_name(la), norm_name(lb)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if na in nb or nb in na:
        return True
    if la.lower().startswith("benchmark-") and lb.lower().startswith("benchmark-"):
        return True
    if "trash-series" in na and "trash-series" in nb:
        return True
    return SequenceMatcher(None, na, nb).ratio() >= 0.65


def path_key(path: list[str]) -> str:
    return " → ".join(path)


def load_assignments(path: Path) -> dict[str, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("assignments") or data
    out: dict[str, list[str]] = {}
    for cid, entry in raw.items():
        if entry.get("path"):
            out[cid] = entry["path"]
        elif entry.get("domain"):
            out[cid] = [entry["domain"], entry["sub"]]
    return out


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    homes = root / "artifacts/catalog/blob_homes_assignments.json"
    kanban = root / "artifacts/catalog/kanban_data.json"
    out_md = root / "artifacts/catalog/ZONE_INBOX_DUPE_REPORT.md"

    assignments = load_assignments(homes)
    cards = {c["id"]: c for c in json.loads(kanban.read_text())["cards"]}
    assigned = [cards[cid] for cid in assignments if cid in cards]

    by_zone: dict[str, list[dict]] = defaultdict(list)
    for cid, path in assignments.items():
        if cid in cards:
            by_zone[path_key(path)].append(cards[cid])

    lines = [
        "# Zone inbox — same size & similar names",
        "",
        f"**Registered placements:** {len(assignments)}",
        "",
        "---",
        "",
        "## Per swim-lane inbox",
        "",
    ]

    similar_groups = 0
    for zone in sorted(by_zone, key=lambda z: -len(by_zone[z])):
        zone_cards = by_zone[zone]
        if len(zone_cards) < 2:
            continue
        by_size: dict[tuple[int, int], list[dict]] = defaultdict(list)
        for c in zone_cards:
            by_size[(c["blobs"], c["bytes"])].append(c)

        twins = [(k, v) for k, v in by_size.items() if len(v) >= 2]
        if not twins:
            continue

        lines.append(f"### `{zone}` — inbox **{len(zone_cards)}**")
        lines.append("")
        for (blobs, nbytes), group in sorted(twins, key=lambda x: -len(x[1])):
            human = group[0].get("bytes_human", "")
            lines.append(f"**Same size:** {blobs:,} files · {human}")
            for c in sorted(group, key=lambda x: x["label"]):
                lines.append(f"- `{c['label']}`")
            sim_pairs = []
            for i, a in enumerate(group):
                for b in group[i + 1 :]:
                    if similar(a["label"], b["label"]):
                        sim_pairs.append((a["label"], b["label"]))
            if sim_pairs:
                similar_groups += 1
                lines.append("- **Similar names:**")
                for a, b in sim_pairs:
                    lines.append(f"  - `{a}` ↔ `{b}`")
            lines.append("")

    lines.extend(["---", "", "## All assigned cards — same size (any zone)", ""])
    by_size_all: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for c in assigned:
        by_size_all[(c["blobs"], c["bytes"])].append(c)
    for (blobs, nbytes), group in sorted(by_size_all.items(), key=lambda x: -len(x[1])):
        if len(group) < 2:
            continue
        lines.append(f"### {blobs:,} files · {group[0].get('bytes_human','')}")
        zones = defaultdict(list)
        for c in group:
            z = path_key(assignments[c["id"]])
            zones[z].append(c["label"])
        for c in sorted(group, key=lambda x: x["label"]):
            lines.append(f"- `{c['label']}` → {path_key(assignments[c['id']])}")
        sp = []
        for i, a in enumerate(group):
            for b in group[i + 1 :]:
                if similar(a["label"], b["label"]):
                    sp.append((a["label"], b["label"]))
        if sp:
            lines.append("- **Similar names:** " + "; ".join(f"`{a}` ↔ `{b}`" for a, b in sp[:6]))
        lines.append("")

    lines.append(f"---\n\n**Lanes with size twins:** {sum(1 for z in by_zone if len(by_zone[z])>=2)} · **Similar-name pairs in lanes:** {similar_groups}\n")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
