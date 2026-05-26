#!/usr/bin/env bash
# Creates DISCO26 container with 5 production folders and labeled sub-folders.
# Each sub-folder gets an INDEX.md placeholder blob.
# No file copying — structure + index only.
#
# Usage:
#   export AZURE_STORAGE_ACCOUNT="menageriesa36965"
#   export AZURE_STORAGE_KEY="<key>"
#   bash scripts/create_disco26_container.sh
set -euo pipefail

: "${AZURE_STORAGE_ACCOUNT:?Set AZURE_STORAGE_ACCOUNT}"
: "${AZURE_STORAGE_KEY:?Set AZURE_STORAGE_KEY}"

CONTAINER="DISCO26"
TMPDIR_LOCAL=$(mktemp -d)
trap 'rm -rf "$TMPDIR_LOCAL"' EXIT

upload_index() {
  local blob_path="$1"
  local title="$2"
  local description="$3"
  local source_path="$4"

  local tmp="$TMPDIR_LOCAL/index.md"
  cat > "$tmp" <<EOF
# ${title}
${description}

## Source location
${source_path}

## Status
Awaiting file copy from source. This folder is a placeholder — see artifacts/DISCOVERY_LOG.md for full path mapping.
EOF

  az storage blob upload \
    --account-name "$AZURE_STORAGE_ACCOUNT" \
    --account-key  "$AZURE_STORAGE_KEY" \
    --container-name "$CONTAINER" \
    --name "${blob_path}/INDEX.md" \
    --file "$tmp" \
    --overwrite \
    --no-progress \
    --output none
  echo "  uploaded: ${blob_path}/INDEX.md"
}

# ── Create container ──────────────────────────────────────────────────────────
echo "Creating container: $CONTAINER"
az storage container create \
  --account-name "$AZURE_STORAGE_ACCOUNT" \
  --account-key  "$AZURE_STORAGE_KEY" \
  --name "$CONTAINER" \
  --output none 2>/dev/null || true
echo "Container ready."
echo ""

# ── PRODUCTION 1 ─────────────────────────────────────────────────────────────
P1="PROD01_RedmondTax000001-008835"
echo "[$P1]"
upload_index "$P1/RedmondTax000001-008835_DOL-CivilWageLitigation" \
  "DOL Civil Wage Litigation Folder" \
  "Dept. of Labor civil wage litigation records. Produced 10/31/24 via USAfx." \
  "Azure: organization/super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/Fed drive/NATIVES/0001/"

upload_index "$P1/RedmondTax000001-008835_RedmondInterview" \
  "Redmond Interview Folder" \
  "Interview records. Produced 10/31/24 via USAfx." \
  "Azure: evidence-federal/redmond-defense-transcripts/"

upload_index "$P1/RedmondTax000001-008835_GrandJuryExhibits" \
  "Grand Jury Exhibit Folder" \
  "GJ exhibit materials. Produced 10/31/24 via USAfx." \
  "Azure: onedrive-personal/01_LEGAL/REDMOND_TRIAL/ (5,683 blobs)"

upload_index "$P1/RedmondTax000001-008835_GuaranteedPayments" \
  "Guaranteed Payments Folder" \
  "Guaranteed payments records. Produced 10/31/24 via USAfx." \
  "Azure: organization/super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/fed teddies/"

upload_index "$P1/RedmondTax000001-008835_IRS" \
  "IRS Folder" \
  "IRS records. Produced 10/31/24 via USAfx." \
  "Azure: financial-docs/ + onedrive-personal/02_FINANCE/"

upload_index "$P1/RedmondTax000001-008835_GrandJuryInterviews" \
  "Grand Jury Interviews" \
  "GJ interview transcripts. Produced 10/31/24 via USAfx." \
  "Azure: evidence-federal/redmond-defense-transcripts/ + analysis/"

upload_index "$P1/RedmondTax000001-008835_CriminalHistory" \
  "Other Files — Redmond Criminal History" \
  "Criminal history records. Produced 10/31/24 via USAfx." \
  "Azure: evidence-federal/redmond-defense-artifacts/"

upload_index "$P1/RedmondTax000001-008835_Indictment-ACA-ReleaseConditions" \
  "Indictment / ACA Article / Release Conditions" \
  "Indictment, ACA article, release conditions. Produced 10/31/24 via USAfx." \
  "Azure: evidence-federal/legal/CASES/ (81 blobs)"

echo ""

# ── PRODUCTION 2 ─────────────────────────────────────────────────────────────
P2="PROD02_RedmondTax000836-693308"
echo "[$P2]"
upload_index "$P2/RedmondTax000836-693308_GJSubpoenaReturns-Financial" \
  "GJ Subpoena Returns — Financial Institutions" \
  "Grand Jury subpoena returns from financial institutions. Produced 01/16/25 via Flash Drive/FedEx." \
  "Azure: organization/backups/onedrive-acct1/Google Drive/DAVID HEIM DISC/1. Discovery_Docket/00 Raw discovery/01_SMALL DISK DISC/DISC_2_2025/FILES/TEXT/0001/"

upload_index "$P2/RedmondTax000836-693308_SeguroMedico" \
  "GJ Subpoena Returns — Seguro Medico" \
  "Seguro Medico subpoena returns. Produced 01/16/25 via Flash Drive/FedEx." \
  "Azure: discovery/EVIDENCE_PULL_ROOT/EVIDENCE_PULL/ (6,961 blobs)"

upload_index "$P2/RedmondTax000836-693308_JohnSardella" \
  "GJ Subpoena Returns — John Sardella" \
  "John Sardella subpoena returns. Produced 01/16/25 via Flash Drive/FedEx." \
  "Azure: organization/super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/feds 2025-01/NATIVES/0003/"

upload_index "$P2/RedmondTax000836-693308_CMalcolmSmith" \
  "GJ Subpoena Returns — C. Malcolm Smith" \
  "C. Malcolm Smith subpoena returns. Produced 01/16/25 via Flash Drive/FedEx." \
  "Azure: organization/super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/"

upload_index "$P2/RedmondTax000836-693308_StephanieMiller" \
  "GJ Subpoena Returns — Stephanie Miller" \
  "Stephanie Miller subpoena returns. Produced 01/16/25 via Flash Drive/FedEx." \
  "Azure: organization/super-master-triage/uploads/google-drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/FINAL FED FUCK YOU copy/Stephanie_Miller/.../NATIVES/0003/"

upload_index "$P2/RedmondTax000836-693308_SharerPetree" \
  "GJ Subpoena Returns — Sharer Petree" \
  "Sharer Petree subpoena returns. Produced 01/16/25 via Flash Drive/FedEx." \
  "Azure: organization/super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/"

upload_index "$P2/RedmondTax000836-693308_MarkPoserina" \
  "GJ Subpoena Returns — Mark Poserina" \
  "Mark Poserina subpoena returns. Produced 01/16/25 via Flash Drive/FedEx." \
  "Azure: organization/super-master-triage/uploads/Google Drive/FED FED 2026 FINAL DISCO/NEW ALAN FEDS/"

echo ""

# ── PRODUCTION 3 ─────────────────────────────────────────────────────────────
P3="PROD03_RedmondOvertActs0001-0722"
echo "[$P3]"
upload_index "$P3/RedmondOvertActs0001-0722_OvertActsRecords" \
  "Records Supporting Overt Acts — Superseding Indictment" \
  "Records supporting overt acts. Produced 07/18/25 via USAfx." \
  "Azure: onedrive-personal/01_LEGAL/SUPERSEDWINSTARTS/ (178 blobs)"

upload_index "$P3/RedmondOvertActs0001-0722_InterviewsTranscripts" \
  "Interviews and Transcripts — Redmond" \
  "Interview transcripts with Redmond. Produced 07/18/25 via USAfx." \
  "Azure: evidence-federal/redmond-defense-transcripts/ (7 blobs)"

upload_index "$P3/RedmondOvertActs0001-0722_CriminalHistory" \
  "Redmond Criminal History" \
  "Redmond criminal history records. Produced 07/18/25 via USAfx." \
  "Azure: evidence-federal/redmond-defense-artifacts/ (17 blobs)"

upload_index "$P3/RedmondOvertActs0001-0722_SearchWarrantAffidavit" \
  "Search Warrant Affidavit and Related Documents" \
  "Search warrant affidavit. Produced 07/18/25 via USAfx." \
  "Azure: evidence-federal/final-FBI-defensive-DOJ-strategy/ (73 blobs) + operation-freedom/assets/ (13 blobs)"

upload_index "$P3/RedmondOvertActs0001-0722_SeguroMedico-Search" \
  "Seguro Medico Search Records" \
  "Records from search of Seguro Medico. Produced 07/18/25 via USAfx." \
  "Azure: evidence-federal/analysis/ (23 blobs)"

upload_index "$P3/RedmondOvertActs0001-0722_CellPhone-Search" \
  "Redmond Cell Phone Search Records" \
  "Records from search of Redmond's cell phone. Produced 07/18/25 via USAfx." \
  "Azure: backups/admin-2026-04-17/rclone-staging/iphone_forensic_20250821T052231Z/"

echo ""

# ── PRODUCTION 4 ─────────────────────────────────────────────────────────────
P4="PROD04_Prod02Confidential"
echo "[$P4]"
upload_index "$P4/Prod02Confidential_000000001-000991938_Five9-CallRecordings" \
  "Five-9 Call Recordings (FIVE9_02_CONFIDENTIAL_AR-*)" \
  "1.1M+ Five-9 sales call recordings. Bates prefix FIVE9_02_CONFIDENTIAL_AR-{NNNNNNN}.wav. Produced 09/29/25 via Hard Drive." \
  "Azure PRIMARY: five9-calls/FIVE9_02_folder/FIVE9_02_CONFIDENTIAL_AR-{N}.wav (57,562 blobs)
Azure FULL EXTRACT: legal/recordings/00_---- DOMAINS/01_LEGAL/FULL EXTRACTIONS/2. FULL EXTRACTION CALL PART 2/{batch}/
Azure TRASH: five9-calls/trash-series02/.Trash/ (~9,102 blobs)
OneDrive mirror: onedrive-personal/OneDrive-Personal/FIVE9_02_CONFIDENTIAL_AR-0000132430 7.wav/ (57,426 blobs)"

upload_index "$P4/Prod02Confidential_000000001-000991938_awalsh413-EmailAccount" \
  "awalsh413@aol.com Account Records" \
  "Full email account records from awalsh413@aol.com. Produced 09/29/25 via Hard Drive." \
  "Azure: backups/onedrive-acct1/ (160,425 blobs)
Nested: backups/onedrive-acct1/onedrive-acct2/ (131,352 blobs)
Google Drive: backups/onedrive-acct1/Google Drive/ (10,748 blobs)"

upload_index "$P4/Prod02Confidential_000000001-000991938_QPH1-HPNotebook" \
  "QPH1 HP Notebook Computer Records" \
  "Full contents of QPH1 HP Notebook. Produced 09/29/25 via Hard Drive." \
  "Azure: backups/admin-2026-04-17/ (15,230 blobs)
AI session data: backups/ai-data-admin-2026-04-17/ (153,802 blobs)
FBI master: backups/admin-2026-04-17/FBI (master)/ (3 blobs)"

upload_index "$P4/RedmondiPhone_00001-09698_iPhone-Cellebrite" \
  "Redmond iPhone — Cellebrite Extraction (RedmondiPhone_00001–09698)" \
  "Redmond iPhone forensic extraction via Cellebrite UFED. Produced 09/29/25 via Hard Drive." \
  "Azure forensic log: backups/admin-2026-04-17/rclone-staging/iphone_forensic_20250821T052231Z/run.log
Cellebrite UFED tiles: backups/onedrive-acct1/FIVE9_02_CONFIDENTIAL_AR-0000132430 7.wav/01_LEGAL/FULL EXTRACTIONS/FIVE9_ 06_CONFIDENTIAL_AR/FIVE9-06 Alan Redmond/IMAGES/0001/FIVE9_06_CONFIDENTIAL_AR-{N}.tif
Trial copies: onedrive-personal/01_LEGAL/REDMOND_TRIAL/ (5,683 blobs)
NOTE: RedmondiPhone bates prefix not in filenames; stored as FIVE9_06_CONFIDENTIAL_AR-*.tif"

echo ""

# ── PRODUCTION 5 ─────────────────────────────────────────────────────────────
P5="PROD05_Prod03Confidential"
echo "[$P5]"
upload_index "$P5/Prod03Confidential_000000001-000677497_Five9-CallRecordings" \
  "Five-9 Call Recordings (FIVE9_03_CONFIDENTIAL_AR-*)" \
  "Five-9 recordings under Prod03_Confidential. Bates FIVE9_03_CONFIDENTIAL_AR-{NNNNNNN}.wav. Produced 03/23/26 via Flash Drive.
GAP: 153,776 AR-IDs confirmed local-only — not yet uploaded to Azure five9-calls container." \
  "Azure (partial): five9-calls/trash-series03/.Trash/FIVE9_03_CONFIDENTIAL_AR-{N}.wav (72,212 blobs)
OneDrive LOCAL ONLY: 01_LEGAL/LEGAL DOMAIN/FULL EXTRACTIONS/3. FULL EXTRACTION CALL PART 3/NATIVES/0001/ (153,776 AR-IDs)"

upload_index "$P5/Prod03Confidential_000000001-000677497_FBI-CasefileSerials" \
  "FBI Casefile Serials and Attachments" \
  "FBI casefile serials including interview reports. Produced 03/23/26 via Flash Drive." \
  "Azure: backups/admin-2026-04-17/FBI (master)/ (3 blobs)
Azure: evidence-federal/final-FBI-defensive-DOJ-strategy/ (73 blobs)
Azure: evidence-federal/redmond-defense-artifacts/ (17 blobs)"

upload_index "$P5/Prod03Confidential_000000001-000677497_iPhone-SelectedRecords" \
  "Selected Records from Redmond iPhone" \
  "Selected iPhone records. Produced 03/23/26 via Flash Drive." \
  "Azure: backups/admin-2026-04-17/rclone-staging/iphone_forensic_20250821T052231Z/
Azure: onedrive-personal/01_LEGAL/REDMOND_TRIAL/ (5,683 blobs)"

upload_index "$P5/Prod03Confidential_000000001-000677497_GrandJuryExhibits" \
  "Grand Jury Exhibits" \
  "Grand Jury exhibit materials. Produced 03/23/26 via Flash Drive." \
  "Azure: onedrive-personal/01_LEGAL/REDMOND_TRIAL/ (5,683 blobs)
Azure: discovery/EVIDENCE_PULL_LEGAL/EVIDENCE_PULL/ (1,720 blobs)"

upload_index "$P5/Prod03Confidential_000000001-000677497_SeguroMedico-Scans" \
  "Scans of Materials Recovered from Seguro Medico" \
  "Physical scans from Seguro Medico search. Produced 03/23/26 via Flash Drive." \
  "Azure: evidence-federal/analysis/evidence/ + analysis/financial/
Azure: discovery/EVIDENCE_PULL_ROOT/EVIDENCE_PULL/ (6,961 blobs)"

upload_index "$P5/Prod03Confidential_000000001-000677497_GJSubpoenaReturns-Financial" \
  "Additional GJ Subpoena Returns — Financial Institutions" \
  "Additional Grand Jury subpoena returns from financial institutions and other businesses. Produced 03/23/26 via Flash Drive." \
  "Azure: discovery/EVIDENCE_PULL_ROOT/EVIDENCE_PULL/ (6,961 blobs)
Azure: organization/super-master-triage/uploads/google-drive/FED FED 2026 FINAL DISCO/FINAL FED FUCK YOU/Stephanie_Miller/.../NATIVES/0003/"

upload_index "$P5/Prod03Confidential_000000001-000677497_MedicoSearchWarrant" \
  "Medico Search Warrant" \
  "Seguro Medico search warrant materials. Produced 03/23/26 via Flash Drive." \
  "Azure: evidence-federal/operation-freedom/assets/ (13 blobs)
Azure: legal-filings/RUSH_SANCTIONS/RUSH SANCTIONS:MOTION EXEMPTIONS/ (8,004 blobs)"

echo ""
echo "Done. DISCO26 container structure created."
echo "Total folders: $(az storage blob list --account-name "$AZURE_STORAGE_ACCOUNT" --account-key "$AZURE_STORAGE_KEY" --container-name "$CONTAINER" --query "length(@)" -o tsv) blobs"
echo ""
echo "Run 'az storage blob list --account-name $AZURE_STORAGE_ACCOUNT --container-name $CONTAINER --output table' to verify."
