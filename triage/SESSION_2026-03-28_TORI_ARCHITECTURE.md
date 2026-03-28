# SESSION TRANSCRIPT — TORI ARCHITECTURE DECISION
## Date: March 28, 2026
## Decision: Azure-First Stack with Custom UI

---

## ARCHITECTURE DECISION

Alan confirmed the final infrastructure stack:

1. **AZURE** = backbone. All infrastructure runs on Microsoft.
2. **GITHUB** = repo management + version control, synced TO Azure (not the reverse).
3. **TORI** = custom UI replacing Azure DevOps dashboards, Boards, Calendar. Wired directly to Azure APIs.
4. **MARK-I** = fleet orchestrator. Single slave process on Azure VM that runs everything.

### WHAT GOT KILLED
- Linear Workspace (PL-030) — DEAD
- Azure DevOps native UI (dashboards, boards, calendar) — DEAD
- All third-party project management — DEAD

### WHAT REPLACES THEM
- Tori = Kanban + Calendar + Dashboard + War Room + Evidence Explorer
- Single Next.js 14+ app on Azure VM
- Reads from Azure DevOps REST API for work items
- Reads from Azure AI Search for evidence
- Reads from PostgreSQL for war room data
- All rendered in Redmond Blueprint design system

### DELIVERABLE PRODUCED
- `tori_architecture.html` — Full exploded assembly blueprint diagram
  - Layer 00: Azure Backbone (VM, Blob, PG, AI Search, Comms)
  - Layer 01: Version Control Pipe (GitHub → Azure sync)
  - Layer 02: Tori Interface (6 modules)
  - Layer 03: Fleet Master (PM2, ANVIL agents, Mark-I orchestrator, MCP)
  - Layer 04: Access Topology (4 entry points)

### REGISTER UPDATES NEEDED
- PL-030 (Linear): Mark KILLED/SUPERSEDED by Tori
- PL-031 (Azure DevOps Kanban): Mark SUPERSEDED — data stays, UI replaced by Tori

---

*Session continues from P0 priorities in previous handoff*
