#!/usr/bin/env bash
# Run all production hunt workers in parallel, then merge.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/azdedup/src"

mkdir -p artifacts/catalog/hunt/{prod01,prod02a,prod02b,prod03,prod04_five9,prod04_docs,prod05}

echo "Starting 7 parallel hunts..."
python3 scripts/production_hunt_worker.py --mode prod01 --all-inventory --out artifacts/catalog/hunt/prod01 &
python3 scripts/production_hunt_worker.py --mode prod02 --shards 00,01,02,03,04 --bates-min 836 --bates-max 350000 --label 836-350000 --out artifacts/catalog/hunt/prod02a &
python3 scripts/production_hunt_worker.py --mode prod02 --shards 05,06,07,08,09 --bates-min 350001 --bates-max 693308 --label 350001-693308 --out artifacts/catalog/hunt/prod02b &
python3 scripts/production_hunt_worker.py --mode prod03 --all-inventory --out artifacts/catalog/hunt/prod03 &
python3 scripts/production_hunt_worker.py --mode prod04-five9-02 --all-inventory --out artifacts/catalog/hunt/prod04_five9 &
python3 scripts/production_hunt_worker.py --mode prod04-docs --all-inventory --out artifacts/catalog/hunt/prod04_docs &
python3 scripts/production_hunt_worker.py --mode prod04-five9-03 --all-inventory --out artifacts/catalog/hunt/prod05 &
wait

echo "PROD05 deep_v4 join (sequential — large)..."
python3 scripts/production_hunt_worker.py --mode prod05-join --all-inventory --out artifacts/catalog/hunt/prod05

echo "Merging..."
python3 scripts/production_hunt_merge.py
echo "Done."
