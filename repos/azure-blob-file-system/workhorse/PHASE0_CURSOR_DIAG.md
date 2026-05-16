# Phase 0 — Cursor quit / crash diagnostics (read-only)

**Date checked:** 2026-04-27

## Summary

- **No Cursor `.ips` crash reports from 2026-04-27** in `~/Library/Logs/DiagnosticReports/` (recent entries are `zsh` and `WeatherMenu` only).
- **Only Cursor-related crash on disk:** `Cursor Helper (Plugin)-2026-04-21-024412.ips` — Electron extension host (`SIGTRAP` / `EXC_BREAKPOINT`), not a filesystem walk.
- **`/usr/bin/log show` (last 6h)** for Cursor shows normal AppKit pasteboard / TextInput noise — **no termination / jetsam / OOM lines** in the tail reviewed.

## Likely cause of “Cursor blew up” during big inventory (hypothesis)

When a full filesystem or blob listing runs **inside** the Cursor-integrated terminal or agent:

1. **Huge stdout/stderr** back into Cursor can overwhelm the UI / IPC (Electron renderer + extension host).
2. **Memory pressure** from buffering output or loading giant MD previews in-editor.
3. **Extension host** instability (see Apr 21 plugin crash) under heavy load.

## 2026-04-27 follow-up: first indexer run stalled

The first `os.walk` attempt under `/Users/stripe_secure` reached **~2.25M files** then the Python process sat in **uninterruptible disk wait** (`STAT=UN`) with **no further log progress** while `index.jsonl` stopped growing. The last paths touched were under **`~/Library/...`** (Google / browser / DriveFS style trees).

**Mitigation applied:** broaden excludes for macOS **`~/Library/{Containers,Application Support,Group Containers,...}`** so the scan stays in user content (Desktop/Documents/Downloads/projects) and avoids FUSE / browser profile tar pits.

## Mitigations we are using for Workhorse inventory

- Run the indexer **detached** (`nohup` + `disown`) so Cursor crashing does **not** kill the job.
- Stream file metadata to **`workhorse/index.jsonl`** on disk; **do not** pipe millions of lines into chat.
- **Exclude** heavy subtrees (`node_modules`, `.git`, caches, `.cursor/extensions`, etc.) per plan.
- **Gitignore** large generated blobs (`index.jsonl`, `five9_azure.jsonl`, logs); commit **summaries only** (`*.md`).

## Commands used (for repeatability)

```bash
ls -lt "$HOME/Library/Logs/DiagnosticReports" | head
ls "$HOME/Library/Logs/DiagnosticReports"/Cursor*.ips 2>/dev/null
/usr/bin/log show --last 6h --predicate 'process == "Cursor" OR process == "Cursor Helper" OR process == "Cursor Helper (Renderer)"' | tail -80
```
