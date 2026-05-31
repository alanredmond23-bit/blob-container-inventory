#!/usr/bin/env python3
"""
scan_all_containers.py — Scan Azure containers for government discovery bates files.
Usage:
  python3 scripts/scan_all_containers.py [--containers c1 c2 ...] [--summary]
  python3 scripts/scan_all_containers.py --iphone   # Quick iPhone extraction check
Requires: AZURE_STORAGE_KEY env var
"""
import argparse, base64, hashlib, hmac, datetime, os, re, sys, json
from urllib.parse import quote, urlparse, parse_qs
from collections import defaultdict
from pathlib import Path

ACCOUNT = os.environ.get("AZURE_STORAGE_ACCOUNT", "menageriesa36965")
KEY_B64 = os.environ.get("AZURE_STORAGE_KEY", "")
if not KEY_B64:
    sys.exit("ERROR: AZURE_STORAGE_KEY env var not set")
KEY = base64.b64decode(KEY_B64)

BATES_PREFIXES = [
    "RedmondTax", "RedmondOvertActs", "Prod02_Confidential",
    "RedmondiPhone", "Prod03_Confidential", "FIVE9_02", "FIVE9_03", "FIVE9_06",
]

# Containers already fully scanned in prior session
ALREADY_SCANNED = {
    "discovery", "uploads", "legal-filings", "five9-calls",
    "recordings", "evidence-federal", "backups", "organization",
    "financial-docs",
}

ALL_54 = [
    "$web","123triageonedrive","1triageworkhorse","45gb-final-onedrive",
    "agent-outputs","backups","benfranklin-dashboard","bin",
    "claude-conversations","claude-memory","claude-skills","cursor-extractions",
    "devops","discovery","evidence-bankruptcy","evidence-family",
    "evidence-federal","evidence-foreclosure","evidence-rush","financial-docs",
    "five9-calls","fleet-sync","future","gmail-takeout","ice-cold-triage",
    "indexes","legal","legal-filings","lil-red-artifacts",
    "localtriage4162026admincomp","loose-files","make-money",
    "marketing-war-command-center","meta-workflow","mirror-test","models",
    "moreonedrive","onedrive-personal","ops-ingest","organization","personal",
    "product-assets","program-files-hd","recordings","redmond-os","save-money",
    "scheduling-2026","secrets","session-extractions","super-master-triage",
    "sys-tweaks-backups","triage","uploads","workhorse-docs",
]


def _sign(url, headers):
    p = urlparse(url)
    ms = sorted((k.lower(), v.strip()) for k, v in headers.items() if k.lower().startswith("x-ms-"))
    ch = "".join(f"{k}:{v}\n" for k, v in ms)
    cr = f"/{ACCOUNT}{p.path}"
    qs = parse_qs(p.query, keep_blank_values=True)
    if qs:
        for qk in sorted(qs): cr += f"\n{qk}:{','.join(sorted(qs[qk]))}"
    sts = "\n".join(["GET","","","","","","","","","","",""]) + "\n" + ch + cr
    sig = base64.b64encode(hmac.new(KEY, sts.encode(), hashlib.sha256).digest()).decode()
    return f"SharedKey {ACCOUNT}:{sig}"


def _list_request(url):
    import requests as req
    now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    h = {"x-ms-date": now, "x-ms-version": "2020-04-08"}
    h["Authorization"] = _sign(url, h)
    r = req.get(url, headers=h, timeout=60)
    return r.text


def get_blob_count(container):
    """Quick count of a container via one prefix-less request."""
    url = f"https://{ACCOUNT}.blob.core.windows.net/{container}?restype=container&comp=list&maxresults=1"
    xml = _list_request(url)
    if "<Error>" in xml:
        return -1
    return None  # need full scan


def targeted_prefix_scan(container, out_dir=None):
    """
    For each bates prefix, issue one paginated list request.
    Memory-safe: accumulates counts only, not full paths (except 3 samples).
    Returns dict: {prefix: {"count": N, "samples": [...], "min_seq": N, "max_seq": N}}
    """
    results = {}
    for pfx in BATES_PREFIXES:
        count = 0
        samples = []
        seqs = []
        marker = ""
        while True:
            mp = f"&marker={quote(marker)}" if marker else ""
            url = (f"https://{ACCOUNT}.blob.core.windows.net/{container}"
                   f"?restype=container&comp=list&maxresults=5000&prefix={quote(pfx)}{mp}")
            xml = _list_request(url)
            if "<Error>" in xml:
                results[pfx] = {"count": 0, "error": xml[:200]}
                break
            names = re.findall(r"<Name>([^<]+)</Name>", xml)
            count += len(names)
            for n in names:
                if len(samples) < 3:
                    samples.append(n)
                m = re.search(r"(\d{4,10})", n.split("/")[-1])
                if m:
                    seqs.append(int(m.group(1)))
            nm = re.search(r"<NextMarker>([^<]+)</NextMarker>", xml)
            if nm and nm.group(1):
                marker = nm.group(1)
            else:
                break
        results[pfx] = {
            "count": count,
            "samples": samples,
            "min_seq": min(seqs) if seqs else None,
            "max_seq": max(seqs) if seqs else None,
        }
        if count:
            print(f"    {pfx}: {count:,} files  range={results[pfx]['min_seq']}–{results[pfx]['max_seq']}", flush=True)
    return results


def full_scan(container, out_dir=None):
    """
    Full scan for small containers. Memory-safe: counts only.
    Returns same schema as targeted_prefix_scan.
    """
    found = defaultdict(lambda: {"count": 0, "samples": [], "seqs": []})
    marker = ""; total = 0
    while True:
        mp = f"&marker={quote(marker)}" if marker else ""
        url = (f"https://{ACCOUNT}.blob.core.windows.net/{container}"
               f"?restype=container&comp=list&maxresults=5000{mp}")
        xml = _list_request(url)
        if "<Error>" in xml:
            print(f"  ERROR: {xml[:300]}", flush=True)
            break
        names = re.findall(r"<Name>([^<]+)</Name>", xml)
        total += len(names)
        for n in names:
            nl = n.lower()
            for pfx in BATES_PREFIXES:
                if pfx.lower() in nl:
                    found[pfx]["count"] += 1
                    if len(found[pfx]["samples"]) < 3:
                        found[pfx]["samples"].append(n)
                    m = re.search(r"(\d{4,10})", n.split("/")[-1])
                    if m: found[pfx]["seqs"].append(int(m.group(1)))
        names.clear()
        nm = re.search(r"<NextMarker>([^<]+)</NextMarker>", xml)
        if nm and nm.group(1): marker = nm.group(1)
        else: break
    results = {}
    for pfx in BATES_PREFIXES:
        d = found[pfx]
        seqs = d["seqs"]
        results[pfx] = {
            "count": d["count"],
            "samples": d["samples"],
            "min_seq": min(seqs) if seqs else None,
            "max_seq": max(seqs) if seqs else None,
        }
    print(f"  total blobs: {total:,}", flush=True)
    return results, total


def iphone_check():
    """Quick confirmation: list backups/admin-2026-04-17/rclone-staging/ prefixes."""
    import requests as req
    container = "backups"
    prefix = "admin-2026-04-17/rclone-staging/"
    url = (f"https://{ACCOUNT}.blob.core.windows.net/{container}"
           f"?restype=container&comp=list&delimiter=/&prefix={quote(prefix)}&maxresults=50")
    xml = _list_request(url)
    dirs = re.findall(r"<BlobPrefix><Name>([^<]+)</Name>", xml)
    blobs = re.findall(r"<Name>([^<]+)</Name>", xml)
    print(f"\n=== iPhone check: backups/{prefix} ===")
    print(f"Subdirs ({len(dirs)}):")
    for d in dirs: print(f"  {d}")
    if "iphone" in xml.lower() or "cellebrite" in xml.lower():
        print("*** iPhone/Cellebrite data CONFIRMED ***")
    # Count blobs in iphone subdir
    for d in dirs:
        if "iphone" in d.lower() or "cellebrite" in d.lower():
            count = 0; marker = ""
            while True:
                mp = f"&marker={quote(marker)}" if marker else ""
                u2 = (f"https://{ACCOUNT}.blob.core.windows.net/{container}"
                      f"?restype=container&comp=list&maxresults=5000&prefix={quote(d)}{mp}")
                x2 = _list_request(u2)
                names = re.findall(r"<Name>([^<]+)</Name>", x2)
                count += len(names)
                nm = re.search(r"<NextMarker>([^<]+)</NextMarker>", x2)
                if nm and nm.group(1): marker = nm.group(1)
                else: break
            print(f"  {d}: {count:,} blobs")
            # Sample
            sample_url = (f"https://{ACCOUNT}.blob.core.windows.net/{container}"
                          f"?restype=container&comp=list&maxresults=5&prefix={quote(d)}")
            sx = _list_request(sample_url)
            snames = re.findall(r"<Name>([^<]+)</Name>", sx)
            for s in snames[:3]: print(f"    sample: {s}")


def scan_container(container, force_full=False, out_dir=None):
    print(f"\n{'='*60}", flush=True)
    print(f"SCANNING: {container}", flush=True)

    # Quick size probe
    url1 = (f"https://{ACCOUNT}.blob.core.windows.net/{container}"
            f"?restype=container&comp=list&maxresults=1")
    xml1 = _list_request(url1)
    if "<Error>" in xml1:
        code = re.search(r"<Code>([^<]+)</Code>", xml1)
        print(f"  SKIP ({code.group(1) if code else 'error'})", flush=True)
        return None, 0

    if force_full:
        results, total = full_scan(container, out_dir)
    else:
        # Use targeted prefix scan (memory-safe for large containers)
        results = targeted_prefix_scan(container, out_dir)
        total = sum(v["count"] for v in results.values())

    any_found = any(v["count"] > 0 for v in results.values())
    if not any_found:
        print(f"  → CLEAN (no bates files)", flush=True)

    # Write JSONL
    if out_dir:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{container}.json"
        with open(out_file, "w") as f:
            json.dump({"container": container, "results": results, "total_bates": total}, f)

    return results, total


def print_summary(all_results):
    print("\n" + "="*80)
    print("FULL COVERAGE SUMMARY — menageriesa36965")
    print("="*80)
    print(f"{'Container':<35} {'RedmondTax':>12} {'OvertActs':>10} {'P02Conf':>8} {'iPhone':>8} {'FIVE9_02':>9} {'FIVE9_03':>9}")
    print("-"*93)
    for container, (results, _) in sorted(all_results.items()):
        if results is None: continue
        rt = results.get("RedmondTax", {}).get("count", 0)
        oa = results.get("RedmondOvertActs", {}).get("count", 0)
        p2 = results.get("Prod02_Confidential", {}).get("count", 0)
        ip = results.get("RedmondiPhone", {}).get("count", 0)
        f2 = results.get("FIVE9_02", {}).get("count", 0)
        f3 = results.get("FIVE9_03", {}).get("count", 0)
        if any([rt, oa, p2, ip, f2, f3]):
            marker = "**"
        else:
            marker = "  "
        print(f"{marker}{container:<33} {rt:>12,} {oa:>10,} {p2:>8,} {ip:>8,} {f2:>9,} {f3:>9,}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--containers", nargs="+", help="Specific containers to scan")
    parser.add_argument("--summary", action="store_true", help="Print summary table only")
    parser.add_argument("--iphone", action="store_true", help="Quick iPhone check in backups")
    parser.add_argument("--skip-scanned", action="store_true", default=True,
                        help="Skip containers already scanned in prior session")
    parser.add_argument("--force-full", action="store_true",
                        help="Force full scan instead of targeted prefix scan")
    parser.add_argument("--out-dir", default="artifacts/scan_results",
                        help="Output directory for JSONL results")
    args = parser.parse_args()

    if args.iphone:
        iphone_check()
        return

    containers = args.containers or ALL_54
    if args.skip_scanned:
        containers = [c for c in containers if c not in ALREADY_SCANNED]

    all_results = {}
    for c in containers:
        results, total = scan_container(c, force_full=args.force_full, out_dir=args.out_dir)
        all_results[c] = (results, total)

    if args.summary or True:
        print_summary(all_results)


if __name__ == "__main__":
    main()
