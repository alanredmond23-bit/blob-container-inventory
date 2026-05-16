# AZURE BLOB FILE SYSTEM

Goal: make Azure Storage feel like a **Mac Finder filesystem**.

## Related repo

- Private inventory hub: [`FINALINDEX2027`](https://github.com/alanredmond23-bit/FINALINDEX2027) (remote name: `finalindex`)
- This repo remains the tooling origin (`origin` → `azure-blob-file-system`).

## Option B (recommended first): Azure Files + guarded Blob mirroring

### What you get
- Finder mounts an **Azure Files** share over SMB (full file semantics).
- AzCopy mirrors selected **Azure Blob containers** into that share and back (guarded two-way).

### Why not mount Blob directly?
Azure Blob is object storage, not a native filesystem. “Folders” are name prefixes. You can still get a Finder-like experience, but it’s either:
- **Option A**: third-party Finder mount for Blob (e.g. Mountain Duck), or
- **Option B**: mirror Blob into Azure Files (this repo).

## Quickstart (Option B)

1) Copy the example config and fill in SAS tokens:

```bash
cp config.example.env config.env
```

2) Pull Azure Files → local (dry-run, then real):

```bash
./sync_files_pull.sh --dry-run
./sync_files_pull.sh
```

3) Mirror a Blob container → Azure Files (dry-run first):

```bash
./sync_blob_to_files.sh --dry-run
./sync_blob_to_files.sh
```

## Safety rails (do these BEFORE delete-capable sync)
- Blob: enable **soft delete + container delete retention + versioning**.
- Azure Files: use **share soft delete** and take **share snapshots**.
- Start with `DELETE_DESTINATION=prompt`.

## Notes
- SMB to Azure Files uses TCP **445**. Many ISPs block it. If blocked, use **P2S VPN + Private Endpoint** to reach it securely.

