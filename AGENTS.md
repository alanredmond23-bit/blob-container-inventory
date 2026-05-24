# AGENTS.md

## Cursor Cloud specific instructions

### Repository Overview

This is a **documentation-only** repository containing implementation planning artifacts for the platform described in `triage/CLAUDE.md`. There is no runnable application server — only:

- **PDF generators**: `triage/build_plan.py` and `triage/build_final_master.py` (Python, requires `reportlab`)
- **Interactive HTML tools**: `triage/predictive-wall-clock.html`, `triage/tori_architecture.html`, `triage/redmond_doctrine_blueprint.html`
- **VM provisioning script**: `triage/setup.sh` (intended for production Azure VM, not local execution)
- **Design assets/docs**: CSS, CSV, PDFs, markdown transcripts

### Running the PDF generators

```bash
cd triage
python3 build_plan.py          # outputs to /home/claude/
python3 build_final_master.py  # outputs to /home/claude/
```

The output directory `/home/claude/` must exist. Create it with `sudo mkdir -p /home/claude && sudo chown $(whoami) /home/claude` if missing.

### Key caveats

- No `requirements.txt` or `package.json` exists in the repo. The only Python dependency is `reportlab` (for PDF generation).
- No automated tests, no linting configuration, no CI/CD pipeline.
- `triage/setup.sh` is a production VM provisioning script — do NOT run it locally.
- `triage/CLAUDE.md` contains Claude Code execution rules for the planned VM deployment — it describes a system not yet built in this repo.
