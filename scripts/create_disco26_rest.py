#!/usr/bin/env python3
"""
Create disco26 container and upload 31 INDEX.md placeholder blobs
using Azure Blob Storage REST API with Shared Key authentication.
No az CLI required.
"""
import base64, hashlib, hmac, datetime, requests, sys, os
ACCOUNT   = os.environ.get("AZURE_STORAGE_ACCOUNT", "menageriesa36965")
KEY_B64   = os.environ["AZURE_STORAGE_KEY"]   # export AZURE_STORAGE_KEY=<key>
CONTAINER = "disco26"   # Azure container names must be lowercase
BASE_URL  = f"https://{ACCOUNT}.blob.core.windows.net"

_KEY = base64.b64decode(KEY_B64)


def _shared_key_auth(method, url, headers, body=b""):
    """
    Compute Azure Blob Storage Shared Key Authorization header.
    https://learn.microsoft.com/azure/storage/common/storage-rest-api-auth
    """
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(url)
    path   = parsed.path   # e.g. /disco26  or  /disco26/folder/INDEX.md

    # ── Canonicalized headers (x-ms-* only, sorted, lowercase) ──────────────
    ms_hdrs = sorted(
        (k.lower(), v.strip())
        for k, v in headers.items()
        if k.lower().startswith("x-ms-")
    )
    canon_headers = "".join(f"{k}:{v}\n" for k, v in ms_hdrs)

    # ── Canonicalized resource ────────────────────────────────────────────────
    canon_resource = f"/{ACCOUNT}{path}"
    qs = parse_qs(parsed.query, keep_blank_values=True)
    if qs:
        for qk in sorted(qs.keys()):
            canon_resource += f"\n{qk.lower()}:{','.join(sorted(qs[qk]))}"

    # ── Standard headers ──────────────────────────────────────────────────────
    content_length = str(len(body)) if body else ""
    content_type   = headers.get("Content-Type", "")
    # Date must be empty when x-ms-date is used
    string_to_sign = "\n".join([
        method,           # VERB
        "",               # Content-Encoding
        "",               # Content-Language
        content_length,   # Content-Length (empty string if no body)
        "",               # Content-MD5
        content_type,     # Content-Type
        "",               # Date  (using x-ms-date instead)
        "",               # If-Modified-Since
        "",               # If-Match
        "",               # If-None-Match
        "",               # If-Unmodified-Since
        "",               # Range
    ]) + "\n" + canon_headers + canon_resource

    sig = base64.b64encode(
        hmac.new(_KEY, string_to_sign.encode("utf-8"), hashlib.sha256).digest()
    ).decode()
    return f"SharedKey {ACCOUNT}:{sig}"


def _ms_headers(extra=None):
    now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    h = {"x-ms-date": now, "x-ms-version": "2020-04-08"}
    if extra:
        h.update(extra)
    return h


def create_container():
    url = f"{BASE_URL}/{CONTAINER}?restype=container"
    headers = _ms_headers()
    headers["Authorization"] = _shared_key_auth("PUT", url, headers, b"")
    r = requests.put(url, headers=headers, data=b"")
    if r.status_code in (201, 409):
        status = "created" if r.status_code == 201 else "already exists"
        print(f"Container {CONTAINER}: {status}")
        return True
    print(f"ERROR creating container: {r.status_code}\n{r.text[:400]}")
    return False


def upload_blob(blob_name: str, content: str) -> bool:
    data = content.encode("utf-8")
    url  = f"{BASE_URL}/{CONTAINER}/{blob_name}"
    headers = _ms_headers({
        "x-ms-blob-type": "BlockBlob",
        "Content-Type": "text/markdown; charset=utf-8",
    })
    headers["Authorization"] = _shared_key_auth("PUT", url, headers, data)
    r = requests.put(url, headers=headers, data=data)
    ok = r.status_code == 201
    sym = "✓" if ok else "✗"
    print(f"  {sym}  {blob_name}" + ("" if ok else f"  [{r.status_code}] {r.text[:120]}"))
    return ok


# ── INDEX content builder ─────────────────────────────────────────────────────

def idx(title, description, source_path):
    return (
        f"# {title}\n\n"
        f"{description}\n\n"
        f"## Source location\n\n"
        f"{source_path}\n\n"
        f"## Status\n\n"
        f"Awaiting file copy from source. This folder is a placeholder —\n"
        f"see artifacts/DISCOVERY_LOG.md for full path mapping.\n\n"
        f"_Protected under Protective Order ECF No. 82 (June 2, 2025)._\n"
    )


# ── Blob manifest ─────────────────────────────────────────────────────────────

P1 = "PROD01_RedmondTax000001-008835"
P2 = "PROD02_RedmondTax000836-693308"
P3 = "PROD03_RedmondOvertActs0001-0722"
P4 = "PROD04_Prod02Confidential"
P5 = "PROD05_Prod03Confidential"

BLOBS = [
    # ── PROD 1 ──────────────────────────────────────────────────────────────
    (f"{P1}/RedmondTax000001-008835_DOL-CivilWageLitigation/INDEX.md",
     idx("DOL Civil Wage Litigation",
         "Dept. of Labor civil wage litigation records. Produced 10/31/24 via USAfx.",
         "Azure: organization/super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/Fed drive/NATIVES/0001/")),

    (f"{P1}/RedmondTax000001-008835_RedmondInterview/INDEX.md",
     idx("Redmond Interview",
         "Interview records. Produced 10/31/24 via USAfx.",
         "Azure: evidence-federal/redmond-defense-transcripts/")),

    (f"{P1}/RedmondTax000001-008835_GrandJuryExhibits/INDEX.md",
     idx("Grand Jury Exhibits",
         "GJ exhibit materials. Produced 10/31/24 via USAfx.",
         "Azure: onedrive-personal/01_LEGAL/REDMOND_TRIAL/ (5,683 blobs)")),

    (f"{P1}/RedmondTax000001-008835_GuaranteedPayments/INDEX.md",
     idx("Guaranteed Payments",
         "Guaranteed payments records. Produced 10/31/24 via USAfx.",
         "Azure: organization/super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/")),

    (f"{P1}/RedmondTax000001-008835_IRS/INDEX.md",
     idx("IRS Records",
         "IRS records. Produced 10/31/24 via USAfx.",
         "Azure: financial-docs/ + onedrive-personal/02_FINANCE/")),

    (f"{P1}/RedmondTax000001-008835_GrandJuryInterviews/INDEX.md",
     idx("Grand Jury Interviews",
         "GJ interview transcripts. Produced 10/31/24 via USAfx.",
         "Azure: evidence-federal/redmond-defense-transcripts/ + analysis/")),

    (f"{P1}/RedmondTax000001-008835_CriminalHistory/INDEX.md",
     idx("Redmond Criminal History",
         "Criminal history records. Produced 10/31/24 via USAfx.",
         "Azure: evidence-federal/redmond-defense-artifacts/")),

    (f"{P1}/RedmondTax000001-008835_Indictment-ACA-ReleaseConditions/INDEX.md",
     idx("Indictment / ACA Article / Release Conditions",
         "Indictment, ACA article, release conditions. Produced 10/31/24 via USAfx.",
         "Azure: evidence-federal/legal/CASES/ (81 blobs)")),

    # ── PROD 2 ──────────────────────────────────────────────────────────────
    (f"{P2}/RedmondTax000836-693308_GJSubpoenaReturns-Financial/INDEX.md",
     idx("GJ Subpoena Returns — Financial Institutions",
         "Grand Jury subpoena returns from financial institutions. Produced 01/16/25 via Flash Drive/FedEx.",
         "Azure: organization/backups/onedrive-acct1/Google Drive/DAVID HEIM DISC/1. Discovery_Docket/00 Raw discovery/01_SMALL DISK DISC/DISC_2_2025/FILES/TEXT/0001/")),

    (f"{P2}/RedmondTax000836-693308_SeguroMedico/INDEX.md",
     idx("GJ Subpoena Returns — Seguro Medico",
         "Seguro Medico subpoena returns. Produced 01/16/25 via Flash Drive/FedEx.",
         "Azure: discovery/EVIDENCE_PULL_ROOT/EVIDENCE_PULL/ (6,961 blobs)")),

    (f"{P2}/RedmondTax000836-693308_JohnSardella/INDEX.md",
     idx("GJ Subpoena Returns — John Sardella",
         "John Sardella subpoena returns. Produced 01/16/25 via Flash Drive/FedEx.",
         "Azure: organization/super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/feds 2025-01/NATIVES/0003/")),

    (f"{P2}/RedmondTax000836-693308_CMalcolmSmith/INDEX.md",
     idx("GJ Subpoena Returns — C. Malcolm Smith",
         "C. Malcolm Smith subpoena returns. Produced 01/16/25 via Flash Drive/FedEx.",
         "Azure: organization/super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/")),

    (f"{P2}/RedmondTax000836-693308_StephanieMiller/INDEX.md",
     idx("GJ Subpoena Returns — Stephanie Miller",
         "Stephanie Miller subpoena returns. Produced 01/16/25 via Flash Drive/FedEx.",
         "Azure: organization/super-master-triage/uploads/google-drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/FINAL FED FUCK YOU copy/Stephanie_Miller/.../NATIVES/0003/")),

    (f"{P2}/RedmondTax000836-693308_SharerPetree/INDEX.md",
     idx("GJ Subpoena Returns — Sharer Petree",
         "Sharer Petree subpoena returns. Produced 01/16/25 via Flash Drive/FedEx.",
         "Azure: organization/super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/")),

    (f"{P2}/RedmondTax000836-693308_MarkPoserina/INDEX.md",
     idx("GJ Subpoena Returns — Mark Poserina",
         "Mark Poserina subpoena returns. Produced 01/16/25 via Flash Drive/FedEx.",
         "Azure: organization/super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/")),

    # ── PROD 3 ──────────────────────────────────────────────────────────────
    (f"{P3}/RedmondOvertActs0001-0722_OvertActsRecords/INDEX.md",
     idx("Records Supporting Overt Acts — Superseding Indictment",
         "Records supporting overt acts. Produced 07/18/25 via USAfx.",
         "Azure: onedrive-personal/01_LEGAL/SUPERSEDWINSTARTS/ (178 blobs)")),

    (f"{P3}/RedmondOvertActs0001-0722_InterviewsTranscripts/INDEX.md",
     idx("Interviews and Transcripts — Redmond",
         "Interview transcripts with Redmond. Produced 07/18/25 via USAfx.",
         "Azure: evidence-federal/redmond-defense-transcripts/ (7 blobs)")),

    (f"{P3}/RedmondOvertActs0001-0722_CriminalHistory/INDEX.md",
     idx("Redmond Criminal History",
         "Redmond criminal history records. Produced 07/18/25 via USAfx.",
         "Azure: evidence-federal/redmond-defense-artifacts/ (17 blobs)")),

    (f"{P3}/RedmondOvertActs0001-0722_SearchWarrantAffidavit/INDEX.md",
     idx("Search Warrant Affidavit and Related Documents",
         "Search warrant affidavit. Produced 07/18/25 via USAfx.",
         "Azure: evidence-federal/final-FBI-defensive-DOJ-strategy/ (73 blobs) + operation-freedom/assets/ (13 blobs)")),

    (f"{P3}/RedmondOvertActs0001-0722_SeguroMedico-Search/INDEX.md",
     idx("Seguro Medico Search Records",
         "Records from search of Seguro Medico. Produced 07/18/25 via USAfx.",
         "Azure: evidence-federal/analysis/ (23 blobs)")),

    (f"{P3}/RedmondOvertActs0001-0722_CellPhone-Search/INDEX.md",
     idx("Redmond Cell Phone Search Records",
         "Records from search of Redmond's cell phone. Produced 07/18/25 via USAfx.",
         "Azure: backups/admin-2026-04-17/rclone-staging/iphone_forensic_20250821T052231Z/")),

    # ── PROD 4 ──────────────────────────────────────────────────────────────
    (f"{P4}/Prod02Confidential_000000001-000991938_Five9-CallRecordings/INDEX.md",
     idx("Five-9 Call Recordings (FIVE9_02_CONFIDENTIAL_AR-*)",
         "1.1M+ Five-9 sales call recordings. Bates prefix FIVE9_02_CONFIDENTIAL_AR-{NNNNNNN}.wav.\nProduced 09/29/25 via Hard Drive.",
         "Azure PRIMARY: five9-calls/FIVE9_02_folder/ (57,562 blobs)\n"
         "Azure FULL EXTRACT: legal/recordings/.../2. FULL EXTRACTION CALL PART 2/{batch}/\n"
         "Azure TRASH: five9-calls/trash-series02/.Trash/ (~9,102 blobs)\n"
         "OneDrive mirror: onedrive-personal/OneDrive-Personal/FIVE9_02_CONFIDENTIAL_AR-*/ (57,426 blobs)")),

    (f"{P4}/Prod02Confidential_000000001-000991938_awalsh413-EmailAccount/INDEX.md",
     idx("awalsh413@aol.com Account Records",
         "Full email account records from awalsh413@aol.com. Produced 09/29/25 via Hard Drive.",
         "Azure: backups/onedrive-acct1/ (160,425 blobs)\n"
         "Nested: backups/onedrive-acct1/onedrive-acct2/ (131,352 blobs)\n"
         "Google Drive: backups/onedrive-acct1/Google Drive/ (10,748 blobs)")),

    (f"{P4}/Prod02Confidential_000000001-000991938_QPH1-HPNotebook/INDEX.md",
     idx("QPH1 HP Notebook Computer Records",
         "Full contents of QPH1 HP Notebook. Produced 09/29/25 via Hard Drive.",
         "Azure: backups/admin-2026-04-17/ (15,230 blobs)\n"
         "AI session data: backups/ai-data-admin-2026-04-17/ (153,802 blobs)\n"
         "FBI master: backups/admin-2026-04-17/FBI (master)/ (3 blobs)")),

    (f"{P4}/RedmondiPhone_00001-09698_iPhone-Cellebrite/INDEX.md",
     idx("Redmond iPhone — Cellebrite Extraction (RedmondiPhone_00001-09698)",
         "Redmond iPhone forensic extraction via Cellebrite UFED. Produced 09/29/25 via Hard Drive.",
         "Azure forensic log: backups/admin-2026-04-17/rclone-staging/iphone_forensic_20250821T052231Z/run.log\n"
         "Cellebrite UFED tiles: backups/onedrive-acct1/.../FIVE9_06_CONFIDENTIAL_AR-{N}.tif\n"
         "Trial copies: onedrive-personal/01_LEGAL/REDMOND_TRIAL/ (5,683 blobs)\n"
         "NOTE: RedmondiPhone bates prefix not in filenames; stored as FIVE9_06_CONFIDENTIAL_AR-*.tif")),

    # ── PROD 5 ──────────────────────────────────────────────────────────────
    (f"{P5}/Prod03Confidential_000000001-000677497_Five9-CallRecordings/INDEX.md",
     idx("Five-9 Call Recordings (FIVE9_03_CONFIDENTIAL_AR-*)",
         "Five-9 recordings under Prod03_Confidential. Bates FIVE9_03_CONFIDENTIAL_AR-{NNNNNNN}.wav.\n"
         "Produced 03/23/26 via Flash Drive.\n"
         "GAP WARNING: 153,776 AR-IDs confirmed local-only — NOT yet uploaded to Azure five9-calls container.",
         "Azure (partial): five9-calls/trash-series03/.Trash/ (72,212 blobs)\n"
         "OneDrive LOCAL ONLY: 01_LEGAL/LEGAL DOMAIN/FULL EXTRACTIONS/3. FULL EXTRACTION CALL PART 3/NATIVES/0001/")),

    (f"{P5}/Prod03Confidential_000000001-000677497_FBI-CasefileSerials/INDEX.md",
     idx("FBI Casefile Serials and Attachments",
         "FBI casefile serials including interview reports. Produced 03/23/26 via Flash Drive.",
         "Azure: backups/admin-2026-04-17/FBI (master)/ (3 blobs)\n"
         "Azure: evidence-federal/final-FBI-defensive-DOJ-strategy/ (73 blobs)\n"
         "Azure: evidence-federal/redmond-defense-artifacts/ (17 blobs)")),

    (f"{P5}/Prod03Confidential_000000001-000677497_iPhone-SelectedRecords/INDEX.md",
     idx("Selected Records from Redmond iPhone",
         "Selected iPhone records. Produced 03/23/26 via Flash Drive.",
         "Azure: backups/admin-2026-04-17/rclone-staging/iphone_forensic_20250821T052231Z/\n"
         "Azure: onedrive-personal/01_LEGAL/REDMOND_TRIAL/ (5,683 blobs)")),

    (f"{P5}/Prod03Confidential_000000001-000677497_GrandJuryExhibits/INDEX.md",
     idx("Grand Jury Exhibits",
         "Grand Jury exhibit materials. Produced 03/23/26 via Flash Drive.",
         "Azure: onedrive-personal/01_LEGAL/REDMOND_TRIAL/ (5,683 blobs)\n"
         "Azure: discovery/EVIDENCE_PULL_LEGAL/EVIDENCE_PULL/ (1,720 blobs)")),

    (f"{P5}/Prod03Confidential_000000001-000677497_SeguroMedico-Scans/INDEX.md",
     idx("Scans of Materials Recovered from Seguro Medico",
         "Physical scans from Seguro Medico search. Produced 03/23/26 via Flash Drive.",
         "Azure: evidence-federal/analysis/evidence/ + analysis/financial/\n"
         "Azure: discovery/EVIDENCE_PULL_ROOT/EVIDENCE_PULL/ (6,961 blobs)")),

    (f"{P5}/Prod03Confidential_000000001-000677497_GJSubpoenaReturns-Financial/INDEX.md",
     idx("Additional GJ Subpoena Returns — Financial Institutions",
         "Additional Grand Jury subpoena returns from financial institutions. Produced 03/23/26 via Flash Drive.",
         "Azure: discovery/EVIDENCE_PULL_ROOT/EVIDENCE_PULL/ (6,961 blobs)\n"
         "Azure: organization/super-master-triage/uploads/google-drive/FED FED 2026 FINAL DISCO/FINAL FED FUCK YOU/Stephanie_Miller/.../NATIVES/0003/")),

    (f"{P5}/Prod03Confidential_000000001-000677497_MedicoSearchWarrant/INDEX.md",
     idx("Medico Search Warrant",
         "Seguro Medico search warrant materials. Produced 03/23/26 via Flash Drive.",
         "Azure: evidence-federal/operation-freedom/assets/ (13 blobs)\n"
         "Azure: legal-filings/RUSH_SANCTIONS/RUSH SANCTIONS:MOTION EXEMPTIONS/ (8,004 blobs)")),
]


def main():
    print(f"Target: {BASE_URL}/{CONTAINER}")
    print(f"Blobs to upload: {len(BLOBS)}")
    print()

    if not create_container():
        sys.exit(1)
    print()

    ok_count = sum(upload_blob(name, content) for name, content in BLOBS)

    print()
    print(f"Done: {ok_count}/{len(BLOBS)} blobs uploaded successfully.")
    if ok_count < len(BLOBS):
        sys.exit(1)


if __name__ == "__main__":
    main()
