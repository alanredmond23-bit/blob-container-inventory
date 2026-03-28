# MENAGERIE AZURE VM -- TRIAGE FOLDER

## CLASSIFICATION: INTERNAL | VERSION 2.0 FINAL | MARCH 2026

---

## WHAT THIS IS

Complete implementation package for deploying the Menagerie platform on a single Azure VM.
Everything in this folder was generated from a single Claude session that covered architecture
decisions, wiring patterns, speed optimization, error prevention, agent swarm design, and
predictive wall clock engineering.

---

## FILE MANIFEST

| File | Purpose |
|------|---------|
| `MENAGERIE_FINAL_MASTER.pdf` | **THE DOCUMENT.** 20-page master plan. Architecture, wiring diagrams, speed layer, 15-error matrix, 6-agent swarm prompts, wall clock system, setup script, CLAUDE.md rules, cost analysis, timeline. Drop into Claude Code. |
| `MENAGERIE_VM_IMPLEMENTATION_PLAN.pdf` | Earlier iteration (v1). Kept for reference. Superseded by FINAL_MASTER. |
| `predictive-wall-clock.html` | Interactive wall clock tool. Open in browser. Select VM tier, agents, enhancements. Start timer on tasks. Self-calibrates from actuals. Persists across sessions. |
| `build_final_master.py` | Python script (ReportLab) that generates FINAL_MASTER.pdf. Run to regenerate. |
| `build_plan.py` | Python script that generates the v1 implementation plan PDF. |
| `CLAUDE.md` | Drop-in rules file for Claude Code. Copy to ~/.claude/CLAUDE.md or project root. |
| `TRANSCRIPT.md` | Full conversation transcript summary with all architectural decisions. |
| `setup.sh` | One-run VM provisioning script. SSH in, run once, walk away 20 min. |

---

## QUICK START

```bash
# 1. Provision VM
az vm create --resource-group menagerie-rg --name menagerie-prod \
  --image Ubuntu2404 --size Standard_D4s_v5 --admin-username alan \
  --generate-ssh-keys --public-ip-sku Standard

# 2. SSH in, run setup
scp setup.sh alan@<VM_IP>:~/
ssh alan@<VM_IP>
bash setup.sh

# 3. Verify
curl -I https://menagerie.yourdomain.com/api/health

# 4. Drop CLAUDE.md into Claude Code workspace
cp CLAUDE.md /path/to/project/.claude/CLAUDE.md
```

---

## ARCHITECTURE SUMMARY

```
TAURI APP ──HTTPS/HTTP2──> NGINX ──> FASTAPI ──> PostgreSQL 16 (local)
                                         |──> Redis 7 (local)
                                         |──> Azure Blob (SAS direct upload)
                                         |──> Azure AI Search (SDK)
                                         |──> Azure OpenAI (SSE streaming)
```

- **VM:** D4s_v5 (4 vCPU, 16GB RAM), Ubuntu 24.04, East US, 24/7
- **Cost:** $241/mo (1yr reserved) all-in
- **Latency:** CRUD <5ms, Search 50-200ms, AI first token ~300ms
- **Protocol:** REST only. SSE for AI streaming. No WebSockets.

---

## GENERATED: March 28, 2026
## AUTHOR: Claude (Anthropic) + Alan (Digital Principles Corp)
