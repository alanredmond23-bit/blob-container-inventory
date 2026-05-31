#!/usr/bin/env python3
"""
Shared Azure scanning library for Five9 / production coverage audit.
All auth via AZURE_STORAGE_KEY env var — never hardcoded.
"""
import base64, hashlib, hmac, datetime, os, re, sys, time
from urllib.parse import quote, urlparse, parse_qs
import requests

ACCOUNT = os.environ.get("AZURE_STORAGE_ACCOUNT", "menageriesa36965")
_KEY_RAW = os.environ.get("AZURE_STORAGE_KEY", "")
KEY = base64.b64decode(_KEY_RAW) if _KEY_RAW else None


def _sign(url: str, headers: dict) -> str:
    p = urlparse(url)
    ms = sorted((k.lower(), v.strip()) for k, v in headers.items()
                if k.lower().startswith("x-ms-"))
    ch = "".join(f"{k}:{v}\n" for k, v in ms)
    cr = f"/{ACCOUNT}{p.path}"
    qs = parse_qs(p.query, keep_blank_values=True)
    if qs:
        for qk in sorted(qs):
            cr += f"\n{qk}:{','.join(sorted(qs[qk]))}"
    sts = "\n".join(["GET", "", "", "", "", "", "", "", "", "", "", ""]) + "\n" + ch + cr
    sig = base64.b64encode(hmac.new(KEY, sts.encode(), hashlib.sha256).digest()).decode()
    return f"SharedKey {ACCOUNT}:{sig}"


def _headers() -> dict:
    now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    return {"x-ms-date": now, "x-ms-version": "2020-04-08"}


def _get(url: str, retries: int = 3) -> str:
    h = _headers()
    h["Authorization"] = _sign(url, h)
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=h, timeout=90)
            return r.text
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return ""


def count_prefix(container: str, prefix: str, verbose: bool = False) -> tuple[int, list[str]]:
    """Streaming count — never accumulates, just increments. Returns (count, samples)."""
    count = 0
    samples = []
    marker = ""
    while True:
        mp = f"&marker={quote(marker)}" if marker else ""
        url = (f"https://{ACCOUNT}.blob.core.windows.net/{container}"
               f"?restype=container&comp=list&maxresults=5000"
               f"&prefix={quote(prefix)}{mp}")
        xml = _get(url)
        names = re.findall(r"<Name>([^<]+)</Name>", xml)
        count += len(names)
        for n in names:
            if len(samples) < 3:
                samples.append(n)
        if verbose and count % 50000 == 0 and count > 0:
            print(f"  {container}/{prefix}: {count:,}...", flush=True)
        nm = re.search(r"<NextMarker>([^<]+)</NextMarker>", xml)
        if nm and nm.group(1):
            marker = nm.group(1)
        else:
            break
    return count, samples


def list_dirs(container: str, prefix: str, max_results: int = 200) -> tuple[list[str], list[str]]:
    """Single API call with delimiter=/ — instant directory enumeration."""
    url = (f"https://{ACCOUNT}.blob.core.windows.net/{container}"
           f"?restype=container&comp=list&delimiter=/&prefix={quote(prefix)}"
           f"&maxresults={max_results}")
    xml = _get(url)
    dirs = re.findall(r"<BlobPrefix><Name>([^<]+)</Name>", xml)
    blobs = re.findall(r"<Name>([^<]+)</Name>", xml)
    return dirs, [b for b in blobs if not b.endswith("/")]


def get_blob_text(container: str, path: str, max_bytes: int = 524288) -> tuple[int, str]:
    """Download blob content up to max_bytes."""
    url = f"https://{ACCOUNT}.blob.core.windows.net/{container}/{quote(path)}"
    h = _headers()
    if max_bytes:
        h["x-ms-range"] = f"bytes=0-{max_bytes - 1}"
    h["Authorization"] = _sign(url, h)
    try:
        r = requests.get(url, headers=h, timeout=60)
        return r.status_code, r.text
    except Exception as e:
        return -1, str(e)


def scan_blob_content_for_terms(container: str, blob_path: str,
                                 terms: list[str], max_bytes: int = 5_000_000) -> dict[str, int]:
    """Read blob in chunks, count occurrences of each term."""
    status, content = get_blob_text(container, blob_path, max_bytes)
    if status != 200 and status != 206:
        return {"_error": status}
    counts = {}
    for term in terms:
        counts[term] = content.count(term)
    return counts


def multi_prefix_scan(container: str, prefixes: list[str]) -> dict[str, tuple[int, list[str]]]:
    """Run count_prefix for each prefix, return dict of results."""
    results = {}
    for p in prefixes:
        count, samples = count_prefix(container, p)
        results[p] = (count, samples)
        print(f"  [{container}] {p!r}: {count:,}  sample={samples[:1]}", flush=True)
    return results


# ── CLI entrypoint ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json, argparse
    parser = argparse.ArgumentParser(description="Five9 / production coverage scanner")
    parser.add_argument("--container", required=True)
    parser.add_argument("--prefixes", nargs="+", default=[])
    parser.add_argument("--blob", help="Path to a blob to read and count terms in")
    parser.add_argument("--terms", nargs="+", default=[])
    parser.add_argument("--list-dirs", metavar="PREFIX", help="List dirs under prefix")
    args = parser.parse_args()

    if not KEY:
        print("ERROR: AZURE_STORAGE_KEY not set", file=sys.stderr)
        sys.exit(1)

    if args.list_dirs is not None:
        dirs, blobs = list_dirs(args.container, args.list_dirs)
        print(json.dumps({"dirs": dirs, "blobs": blobs[:20]}))
    elif args.blob and args.terms:
        counts = scan_blob_content_for_terms(args.container, args.blob, args.terms)
        print(json.dumps(counts))
    elif args.prefixes:
        results = multi_prefix_scan(args.container, args.prefixes)
        out = {p: {"count": c, "samples": s} for p, (c, s) in results.items()}
        print(json.dumps(out, indent=2))
    else:
        parser.print_help()
