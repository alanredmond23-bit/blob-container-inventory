#!/usr/bin/env bash
# Rejoin split Alansinv part 0 for tools expecting a single CSV path.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AG1="$ROOT/artifacts/dedup/ag1"
OUT="$AG1/Alansinv_1000000_0.csv"
if [[ -f "$OUT" ]]; then
  echo "Already exists: $OUT"
  exit 0
fi
cat "$AG1/Alansinv_1000000_0.0.csv" "$AG1/Alansinv_1000000_0.1.csv" > "$OUT"
ls -lh "$OUT"
