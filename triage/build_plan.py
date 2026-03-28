#!/usr/bin/env python3
"""
MENAGERIE AZURE VM IMPLEMENTATION PLAN
McKinsey-grade PDF with full architecture, agent swarm, error prevention
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib import colors
from reportlab.platypus.flowables import Flowable
from datetime import datetime

# ─── COLORS ───
NAVY = HexColor("#050810")
DARK_SLATE = HexColor("#0F172A")
SLATE = HexColor("#1E293B")
MID_SLATE = HexColor("#334155")
LIGHT_SLATE = HexColor("#94A3B8")
BLUE = HexColor("#3B82F6")
CYAN = HexColor("#06B6D4")
GREEN = HexColor("#10B981")
AMBER = HexColor("#F59E0B")
RED = HexColor("#EF4444")
PURPLE = HexColor("#8B5CF6")
WHITE_TEXT = HexColor("#F8FAFC")
BODY_TEXT = HexColor("#1E293B")
LIGHT_BG = HexColor("#F1F5F9")
BORDER_GRAY = HexColor("#CBD5E1")

# ─── STYLES ───
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    'CoverTitle', parent=styles['Title'],
    fontSize=32, leading=38, textColor=white,
    alignment=TA_CENTER, spaceAfter=12,
    fontName='Helvetica-Bold'
))
styles.add(ParagraphStyle(
    'CoverSub', parent=styles['Normal'],
    fontSize=14, leading=18, textColor=LIGHT_SLATE,
    alignment=TA_CENTER, spaceAfter=6,
    fontName='Helvetica'
))
styles.add(ParagraphStyle(
    'SectionHead', parent=styles['Heading1'],
    fontSize=20, leading=24, textColor=BLUE,
    spaceBefore=20, spaceAfter=12,
    fontName='Helvetica-Bold',
    borderWidth=0, borderColor=BLUE,
    borderPadding=0
))
styles.add(ParagraphStyle(
    'SubHead', parent=styles['Heading2'],
    fontSize=14, leading=18, textColor=DARK_SLATE,
    spaceBefore=14, spaceAfter=8,
    fontName='Helvetica-Bold'
))
styles.add(ParagraphStyle(
    'SubHead3', parent=styles['Heading3'],
    fontSize=12, leading=15, textColor=MID_SLATE,
    spaceBefore=10, spaceAfter=6,
    fontName='Helvetica-Bold'
))
styles.add(ParagraphStyle(
    'Body', parent=styles['Normal'],
    fontSize=10, leading=14, textColor=BODY_TEXT,
    spaceAfter=8, alignment=TA_JUSTIFY,
    fontName='Helvetica'
))
styles.add(ParagraphStyle(
    'CodeBlock', parent=styles['Normal'],
    fontSize=8.5, leading=11, textColor=HexColor("#1E293B"),
    fontName='Courier', spaceAfter=6,
    backColor=LIGHT_BG, borderWidth=1,
    borderColor=BORDER_GRAY, borderPadding=6,
    leftIndent=12, rightIndent=12
))
styles.add(ParagraphStyle(
    'CodeSmall', parent=styles['Normal'],
    fontSize=7.5, leading=10, textColor=HexColor("#1E293B"),
    fontName='Courier', spaceAfter=6,
    backColor=LIGHT_BG, borderWidth=1,
    borderColor=BORDER_GRAY, borderPadding=6,
    leftIndent=12, rightIndent=12
))
styles.add(ParagraphStyle(
    'BulletPt', parent=styles['Normal'],
    fontSize=10, leading=14, textColor=BODY_TEXT,
    spaceAfter=4, fontName='Helvetica',
    leftIndent=20, bulletIndent=8
))
styles.add(ParagraphStyle(
    'DiagramText', parent=styles['Normal'],
    fontSize=8, leading=10, textColor=DARK_SLATE,
    fontName='Courier', alignment=TA_LEFT,
    spaceAfter=4, leftIndent=20, rightIndent=20
))
styles.add(ParagraphStyle(
    'TableHeader', parent=styles['Normal'],
    fontSize=9, leading=12, textColor=white,
    fontName='Helvetica-Bold', alignment=TA_CENTER
))
styles.add(ParagraphStyle(
    'TableCell', parent=styles['Normal'],
    fontSize=9, leading=12, textColor=BODY_TEXT,
    fontName='Helvetica'
))
styles.add(ParagraphStyle(
    'Warning', parent=styles['Normal'],
    fontSize=10, leading=14, textColor=HexColor("#92400E"),
    fontName='Helvetica-Bold', spaceAfter=8,
    backColor=HexColor("#FEF3C7"), borderWidth=1,
    borderColor=AMBER, borderPadding=8,
    leftIndent=12, rightIndent=12
))
styles.add(ParagraphStyle(
    'Success', parent=styles['Normal'],
    fontSize=10, leading=14, textColor=HexColor("#065F46"),
    fontName='Helvetica', spaceAfter=8,
    backColor=HexColor("#D1FAE5"), borderWidth=1,
    borderColor=GREEN, borderPadding=8,
    leftIndent=12, rightIndent=12
))

def make_table(headers, rows, col_widths=None, header_color=DARK_SLATE):
    """Build a styled table."""
    hdr = [Paragraph(h, styles['TableHeader']) for h in headers]
    data = [hdr]
    for row in rows:
        data.append([Paragraph(str(c), styles['TableCell']) for c in row])

    if col_widths is None:
        col_widths = [6.5 * inch / len(headers)] * len(headers)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t

def hr():
    return HRFlowable(width="100%", thickness=1, color=BORDER_GRAY,
                      spaceBefore=8, spaceAfter=8)

def diagram_block(lines):
    """Render a text-based diagram."""
    elements = []
    for line in lines:
        safe = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        elements.append(Paragraph(safe, styles['DiagramText']))
    return elements

# ─── BUILD DOCUMENT ───
doc = SimpleDocTemplate(
    "/home/claude/MENAGERIE_VM_IMPLEMENTATION_PLAN.pdf",
    pagesize=letter,
    topMargin=0.6*inch, bottomMargin=0.6*inch,
    leftMargin=0.75*inch, rightMargin=0.75*inch
)

story = []

# ═══════════════════════════════════════════════
# COVER PAGE
# ═══════════════════════════════════════════════

# Dark cover block
cover_data = [[""]]
cover_table = Table(cover_data, colWidths=[7*inch], rowHeights=[3.5*inch])
cover_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), NAVY),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(Spacer(1, 1.5*inch))

story.append(Paragraph("MENAGERIE", styles['CoverTitle']))
story.append(Paragraph("AZURE VM IMPLEMENTATION PLAN", styles['CoverTitle']))
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph("Single-VM Architecture  |  6-Agent Claude Code Swarm  |  World-Class Wiring", styles['CoverSub']))
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph(f"Digital Principles Corp  |  {datetime.now().strftime('%B %d, %Y')}", styles['CoverSub']))
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph("CLASSIFICATION: INTERNAL  |  VERSION 1.0", styles['CoverSub']))

story.append(Spacer(1, 1*inch))
story.append(hr())
story.append(Paragraph(
    "This document contains the complete implementation specification for deploying "
    "the Menagerie platform on a single Azure VM with 24/7 uptime, world-class HTTP "
    "performance, and a 6-agent Claude Code deployment swarm. Designed to be dropped "
    "directly into Claude Code as an execution plan.",
    styles['Body']
))
story.append(PageBreak())

# ═══════════════════════════════════════════════
# TABLE OF CONTENTS
# ═══════════════════════════════════════════════
story.append(Paragraph("TABLE OF CONTENTS", styles['SectionHead']))
story.append(hr())

toc_items = [
    ("01", "Executive Summary", "Architecture decisions, cost, timeline"),
    ("02", "Architecture Overview", "VM stack, service topology, data flow"),
    ("03", "Wiring Diagrams", "Request flow, upload pipeline, AI pipeline"),
    ("04", "World-Class Speed Layer", "HTTP/2, connection pooling, compression"),
    ("05", "Error Prevention Matrix", "Pre-launch error catalog with mitigations"),
    ("06", "6-Agent Claude Code Swarm", "Agent roles, rules, prompts, coordination"),
    ("07", "Full Setup Script", "One-run provisioning script for the VM"),
    ("08", "Claude Code Drop-In Rules", "CLAUDE.md rules file for execution"),
    ("09", "Cost Analysis", "Monthly burn, reserved pricing, optimization"),
    ("10", "Implementation Timeline", "30-min to 2-hour execution blocks"),
]

toc_rows = []
for num, title, desc in toc_items:
    toc_rows.append([num, title, desc])

story.append(make_table(
    ["#", "Section", "Coverage"],
    toc_rows,
    col_widths=[0.5*inch, 2.2*inch, 3.8*inch]
))
story.append(PageBreak())

# ═══════════════════════════════════════════════
# 01 — EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════
story.append(Paragraph("01  EXECUTIVE SUMMARY", styles['SectionHead']))
story.append(hr())

story.append(Paragraph(
    "The Menagerie platform deploys on a single Azure D4s_v5 VM (4 vCPU, 16GB RAM) "
    "running 24/7. All services run on one machine: Nginx reverse proxy, FastAPI application "
    "server, PostgreSQL 16 (51 tables), and Redis cache. External Azure services (Blob Storage, "
    "AI Search, Azure OpenAI) are called via SDK from the VM. The ANVIL fleet (three M1 MacBook Pros) "
    "is fully replaced by this VM.",
    styles['Body']
))

story.append(Paragraph("Key Decisions", styles['SubHead']))

decisions = [
    ["Decision", "Choice", "Rationale"],
]
decision_rows = [
    ["Compute", "Single VM (D4s_v5)", "Always hot, no cold starts, sub-5ms local DB"],
    ["API Framework", "FastAPI + uvicorn", "Async, streaming SSE, 4 workers, auto-restart"],
    ["Database", "PostgreSQL 16 (local)", "Zero-latency queries, pgvector for embeddings"],
    ["Cache", "Redis (local)", "Sub-1ms reads, session/query cache"],
    ["File Storage", "Azure Blob (external)", "Durable, SAS token direct upload"],
    ["Search", "Azure AI Search (external)", "Managed indexing, semantic search"],
    ["AI", "Azure OpenAI (external)", "GPT-4o/Claude streaming via SSE"],
    ["Reverse Proxy", "Nginx + HTTP/2", "TLS termination, compression, multiplexing"],
    ["Frontend", "Tauri (Rust + Web)", "Native desktop, single HTTP client"],
    ["Deploy", "SSH + git pull + systemctl", "10-second deploys, no CI/CD overhead"],
]

story.append(make_table(
    ["Decision", "Choice", "Rationale"],
    decision_rows,
    col_widths=[1.2*inch, 2*inch, 3.3*inch]
))

story.append(Spacer(1, 12))
story.append(Paragraph("Cost Summary", styles['SubHead']))

cost_rows = [
    ["Azure VM D4s_v5 (reserved 1yr)", "$85/mo", "4 vCPU, 16GB, always on"],
    ["Azure Blob Storage", "$10/mo", "100GB estimated"],
    ["Azure AI Search (Basic)", "$75/mo", "1 replica, 1 partition"],
    ["Azure OpenAI", "~$50/mo", "Usage-based, streaming"],
    ["Domain + TLS (Certbot)", "$0/mo", "Let's Encrypt free"],
    ["TOTAL", "$220/mo", "Reserved pricing, all-in"],
]

story.append(make_table(
    ["Service", "Cost", "Notes"],
    cost_rows,
    col_widths=[2.5*inch, 1*inch, 3*inch]
))

story.append(PageBreak())

# ═══════════════════════════════════════════════
# 02 — ARCHITECTURE OVERVIEW
# ═══════════════════════════════════════════════
story.append(Paragraph("02  ARCHITECTURE OVERVIEW", styles['SectionHead']))
story.append(hr())

story.append(Paragraph("Service Topology", styles['SubHead']))

story.extend(diagram_block([
    "============================================================",
    "                    MENAGERIE VM STACK",
    "============================================================",
    "",
    "  TAURI DESKTOP APP (Rust + WebView)",
    "       |",
    "       | HTTPS (HTTP/2, TLS 1.3, keep-alive)",
    "       |",
    "  [NGINX] ---- reverse proxy, gzip/brotli, rate limit",
    "       |",
    "  [FASTAPI] -- uvicorn, 4 workers, systemd managed",
    "       |",
    "       +-------+-------+-------+-------+",
    "       |       |       |       |       |",
    "    [PG 16] [REDIS] [BLOB]  [AI     [AZURE",
    "    local   local   SDK    SEARCH]  OPENAI]",
    "    51 tbl  cache   SAS    SDK      streaming",
    "    pgvec   <1ms    token  50-200ms SSE",
    "    <5ms           upload",
    "",
    "============================================================",
    "  BACKGROUND WORKERS (asyncio / Celery)",
    "    - Vectorization (Azure OpenAI embeddings)",
    "    - Index updates (AI Search push)",
    "    - Backup cron (pg_dump -> Blob nightly)",
    "============================================================",
]))

story.append(Paragraph("Endpoint Map", styles['SubHead']))

endpoint_rows = [
    ["POST /api/auth/token", "Issue JWT", "GREEN", "<10ms"],
    ["GET /api/health", "Health check", "GREEN", "<1ms"],
    ["POST /api/crud/{table}", "Create record", "YELLOW", "<10ms"],
    ["GET /api/crud/{table}/{id}", "Read record", "GREEN", "<5ms"],
    ["PUT /api/crud/{table}/{id}", "Update record", "YELLOW", "<10ms"],
    ["DELETE /api/crud/{table}/{id}", "Delete record", "RED", "<10ms"],
    ["POST /api/upload/sas", "Generate SAS token", "GREEN", "<5ms"],
    ["POST /api/upload/confirm", "Confirm + trigger vectorize", "YELLOW", "<10ms"],
    ["POST /api/search", "AI Search query", "GREEN", "50-200ms"],
    ["POST /api/chat", "AI chat (SSE stream)", "GREEN", "300ms TTFT"],
    ["GET /api/vectors/{doc_id}", "Get embeddings", "GREEN", "<20ms"],
    ["POST /api/batch/vectorize", "Batch vectorize (async)", "YELLOW", "Async"],
    ["GET /api/jobs/{job_id}", "Check async job status", "GREEN", "<5ms"],
]

story.append(make_table(
    ["Endpoint", "Purpose", "Zone", "Target Latency"],
    endpoint_rows,
    col_widths=[2*inch, 1.5*inch, 0.8*inch, 1.2*inch]
))

story.append(PageBreak())

# ═══════════════════════════════════════════════
# 03 — WIRING DIAGRAMS
# ═══════════════════════════════════════════════
story.append(Paragraph("03  WIRING DIAGRAMS", styles['SectionHead']))
story.append(hr())

story.append(Paragraph("Diagram A: Standard CRUD Request Flow", styles['SubHead']))
story.extend(diagram_block([
    "  TAURI                    VM",
    "    |                       |",
    "    |-- POST /api/crud ---->|",
    "    |   {table: 'pets',     |",
    "    |    data: {...}}        |",
    "    |                       |",
    "    |                  [NGINX]",
    "    |                    |  HTTP/2 demux",
    "    |                    |  gzip decompress",
    "    |                    |",
    "    |                 [FASTAPI]",
    "    |                    |  validate input",
    "    |                    |  check Redis cache",
    "    |                    |     HIT? -> return cached",
    "    |                    |     MISS? -> query Postgres",
    "    |                    |  write to Postgres (<5ms)",
    "    |                    |  invalidate Redis key",
    "    |                    |  gzip response",
    "    |                    |",
    "    |<-- 200 OK ---------|",
    "    |   {id: 42, ...}    |",
    "    |                       |",
    "  TOTAL: 10-20ms end-to-end",
]))

story.append(Spacer(1, 12))
story.append(Paragraph("Diagram B: File Upload Pipeline (SAS Direct)", styles['SubHead']))
story.extend(diagram_block([
    "  TAURI                    VM                    AZURE BLOB",
    "    |                       |                        |",
    "    |-- POST /upload/sas -->|                        |",
    "    |   {filename, size}    |                        |",
    "    |                       |                        |",
    "    |                  [generate SAS token, 2ms]     |",
    "    |                       |                        |",
    "    |<-- {sas_url, token} --|                        |",
    "    |                       |                        |",
    "    |-- PUT (file bytes) ---|----------------------->|",
    "    |   direct-to-blob      |   (bypasses VM)       |",
    "    |                       |                        |",
    "    |<-- 201 Created -------|------------------------|",
    "    |                       |                        |",
    "    |-- POST /upload/confirm|                        |",
    "    |   {blob_url}          |                        |",
    "    |                  [save metadata to PG]         |",
    "    |                  [trigger async vectorize]     |",
    "    |                       |                        |",
    "    |<-- 202 Accepted ------|                        |",
    "    |   {job_id}            |                        |",
    "    |                       |                        |",
    "  USER SEES: instant upload (file never touches VM)",
]))

story.append(Spacer(1, 12))
story.append(Paragraph("Diagram C: AI Chat Streaming (SSE)", styles['SubHead']))
story.extend(diagram_block([
    "  TAURI                    VM                    AZURE OPENAI",
    "    |                       |                        |",
    "    |-- POST /api/chat ---->|                        |",
    "    |   {prompt, context}   |                        |",
    "    |                       |                        |",
    "    |                  [build messages array]        |",
    "    |                  [fetch context from PG/Redis] |",
    "    |                  [call Azure OpenAI stream]    |",
    "    |                       |-- stream request ----->|",
    "    |                       |                        |",
    "    |<-- SSE: token 1 ------|<-- chunk 1 ------------|",
    "    |<-- SSE: token 2 ------|<-- chunk 2 ------------|",
    "    |<-- SSE: token 3 ------|<-- chunk 3 ------------|",
    "    |       ...              |       ...              |",
    "    |<-- SSE: [DONE] -------|<-- finish_reason:stop --|",
    "    |                       |                        |",
    "  USER SEES: first token in ~300ms, text streams live",
]))

story.append(PageBreak())

story.append(Paragraph("Diagram D: Background Vectorization Pipeline", styles['SubHead']))
story.extend(diagram_block([
    "  [UPLOAD CONFIRM triggers]",
    "       |",
    "       v",
    "  [ASYNC WORKER]",
    "       |",
    "       +-- 1. Fetch blob from Azure Blob Storage",
    "       |",
    "       +-- 2. Extract text (pdfplumber / python-docx / etc)",
    "       |",
    "       +-- 3. Chunk text (512 token windows, 50 overlap)",
    "       |",
    "       +-- 4. Call Azure OpenAI Embeddings API",
    "       |      model: text-embedding-3-large",
    "       |      dimensions: 3072",
    "       |",
    "       +-- 5. Store vectors in PostgreSQL (pgvector)",
    "       |      INSERT INTO embeddings (doc_id, chunk, vector)",
    "       |",
    "       +-- 6. Push to Azure AI Search index",
    "       |      POST /indexes/docs/docs/index",
    "       |",
    "       +-- 7. Update job status -> 'completed'",
    "       |",
    "       +-- 8. Notify via WebSocket/SSE (optional)",
    "",
    "  TOTAL: 5-30 seconds per document (user never waits)",
]))

story.append(PageBreak())

# ═══════════════════════════════════════════════
# 04 — WORLD-CLASS SPEED LAYER
# ═══════════════════════════════════════════════
story.append(Paragraph("04  WORLD-CLASS SPEED LAYER", styles['SectionHead']))
story.append(hr())

story.append(Paragraph(
    "Three configuration-level changes that drop subsequent request latency from "
    "80-120ms to 5-15ms. No code changes. No architecture changes. Pure config.",
    styles['Body']
))

story.append(Paragraph("Optimization 1: HTTP/2 Multiplexing", styles['SubHead']))
story.append(Paragraph(
    "HTTP/1.1 opens a new TCP+TLS connection per request (50-150ms handshake overhead). "
    "HTTP/2 opens ONE persistent connection and multiplexes all requests through it. "
    "First request pays the handshake. Every subsequent request: near-zero overhead.",
    styles['Body']
))
story.append(Paragraph(
    "listen 443 ssl http2;<br/>"
    "ssl_certificate /etc/letsencrypt/live/DOMAIN/fullchain.pem;<br/>"
    "ssl_certificate_key /etc/letsencrypt/live/DOMAIN/privkey.pem;<br/>"
    "ssl_protocols TLSv1.3;<br/>"
    "ssl_prefer_server_ciphers off;",
    styles['CodeBlock']
))

story.append(Paragraph("Optimization 2: Connection Pooling (Tauri Side)", styles['SubHead']))
story.append(Paragraph(
    "Never create a new HTTP client per request. Hold a single reqwest::Client for "
    "the entire application lifetime. It pools connections automatically.",
    styles['Body']
))
story.append(Paragraph(
    "// In Tauri Rust backend:<br/>"
    "lazy_static! {<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;static ref CLIENT: reqwest::Client = reqwest::Client::builder()<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;.http2_prior_knowledge()<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;.pool_max_idle_per_host(10)<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;.tcp_keepalive(Duration::from_secs(60))<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;.build().unwrap();<br/>"
    "}",
    styles['CodeBlock']
))

story.append(Paragraph("Optimization 3: Response Compression", styles['SubHead']))
story.append(Paragraph(
    "Enable gzip/brotli on Nginx. JSON responses compress 70-80%. A 50KB response "
    "becomes 10KB on the wire. Tauri's reqwest decompresses automatically.",
    styles['Body']
))
story.append(Paragraph(
    "gzip on;<br/>"
    "gzip_vary on;<br/>"
    "gzip_proxied any;<br/>"
    "gzip_comp_level 6;<br/>"
    "gzip_types application/json text/plain text/css application/javascript;<br/>"
    "gzip_min_length 256;",
    styles['CodeBlock']
))

story.append(Spacer(1, 12))
story.append(Paragraph("Latency Impact", styles['SubHead']))

latency_rows = [
    ["CRUD read (cached)", "80-120ms", "<1ms", "Redis localhost"],
    ["CRUD read (DB)", "80-120ms", "<5ms", "Postgres localhost"],
    ["CRUD write", "100-150ms", "<10ms", "Postgres localhost"],
    ["File upload (10MB)", "5-10s", "<2s", "SAS direct-to-blob"],
    ["Search query", "300-500ms", "50-200ms", "AI Search, no middleware hop"],
    ["AI first token", "1-3s", "~300ms", "SSE streaming"],
    ["Subsequent HTTP call", "80-120ms", "5-15ms", "HTTP/2 + keep-alive"],
]

story.append(make_table(
    ["Operation", "Before", "After", "Why"],
    latency_rows,
    col_widths=[1.5*inch, 1*inch, 1*inch, 3*inch]
))

story.append(PageBreak())

# ═══════════════════════════════════════════════
# 05 — ERROR PREVENTION MATRIX
# ═══════════════════════════════════════════════
story.append(Paragraph("05  ERROR PREVENTION MATRIX", styles['SectionHead']))
story.append(hr())

story.append(Paragraph(
    "Every known failure mode cataloged with prevention strategy. No errors during dev. "
    "Fix them before they happen.",
    styles['Body']
))

error_rows = [
    ["E-001", "VM cold boot after restart", "HIGH",
     "systemd services with Restart=always + WantedBy=multi-user.target. "
     "All services auto-start on boot. Test: sudo reboot, verify all services up."],
    ["E-002", "Postgres connection exhaustion", "HIGH",
     "PgBouncer or max_connections=200 in postgresql.conf. FastAPI uses connection pool "
     "(asyncpg pool, min=5, max=20). Never open raw connections."],
    ["E-003", "Disk fills up", "HIGH",
     "Never store uploads on VM. All files to Blob. Log rotation: logrotate.d config, "
     "7-day retention, compress. Monitoring: Azure disk alert at 80%."],
    ["E-004", "SSL cert expires", "MEDIUM",
     "Certbot auto-renewal cron: 0 0 1 * * certbot renew --nginx. "
     "Test: certbot renew --dry-run after setup."],
    ["E-005", "FastAPI crashes", "MEDIUM",
     "systemd Restart=always, RestartSec=3. Uvicorn --workers 4 (one dies, three serve). "
     "Health check endpoint + UptimeRobot alert."],
    ["E-006", "Redis OOM", "LOW",
     "maxmemory 2gb + maxmemory-policy allkeys-lru in redis.conf. "
     "Redis evicts least-used keys automatically."],
    ["E-007", "CORS errors from Tauri", "HIGH",
     "Nginx add_header Access-Control-Allow-Origin for Tauri origin. "
     "Include in setup script. Test with curl -H 'Origin: tauri://localhost'."],
    ["E-008", "Large file upload timeout", "MEDIUM",
     "SAS token pattern bypasses VM entirely. Tauri uploads direct to Blob. "
     "Nginx client_max_body_size only matters for non-file endpoints (set 10m)."],
    ["E-009", "Azure OpenAI rate limit (429)", "MEDIUM",
     "Exponential backoff in SDK call (tenacity library). Queue requests in Redis. "
     "Fallback: route to Anthropic API if Azure throttles."],
    ["E-010", "SSH brute force", "HIGH",
     "NSG: allow SSH only from your IP. fail2ban installed. "
     "SSH key auth only, password auth disabled."],
    ["E-011", "Postgres data loss", "CRITICAL",
     "Nightly pg_dump cron to Blob storage. Azure VM disk snapshots weekly. "
     "Test restore monthly."],
    ["E-012", "Background worker silent failure", "MEDIUM",
     "Job status table in Postgres. Workers update status on start/complete/fail. "
     "Stale job detector: any job 'running' > 10min = alert."],
    ["E-013", "DNS propagation delay", "LOW",
     "Set low TTL (300s) on A record before migration. "
     "During transition, allow both IP and domain access."],
    ["E-014", "Python dependency conflict", "LOW",
     "Use venv for FastAPI. Pin all versions in requirements.txt. "
     "Never pip install globally."],
    ["E-015", "Azure SDK auth token expiry", "MEDIUM",
     "Use DefaultAzureCredential with managed identity on VM. "
     "Tokens auto-refresh. Never hardcode keys in code."],
]

for i in range(0, len(error_rows), 8):
    batch = error_rows[i:i+8]
    story.append(make_table(
        ["ID", "Failure Mode", "Risk", "Prevention + Mitigation"],
        batch,
        col_widths=[0.5*inch, 1.5*inch, 0.6*inch, 3.9*inch]
    ))
    story.append(Spacer(1, 8))

story.append(PageBreak())

# ═══════════════════════════════════════════════
# 06 — 6-AGENT CLAUDE CODE SWARM
# ═══════════════════════════════════════════════
story.append(Paragraph("06  6-AGENT CLAUDE CODE SWARM", styles['SectionHead']))
story.append(hr())

story.append(Paragraph(
    "Six specialized Claude Code agents execute in parallel. Each agent has a single "
    "responsibility, its own workspace rules, and a completion target. No agent touches "
    "another agent's files. Coordination via a shared STATUS.md file.",
    styles['Body']
))

story.append(Paragraph("Agent Roster", styles['SubHead']))

agent_rows = [
    ["AGENT 1", "INFRA", "VM provisioning, Nginx, systemd, firewall, TLS",
     "GREEN", "30 min",
     "az CLI, SSH, systemd, certbot, ufw"],
    ["AGENT 2", "DATABASE", "PostgreSQL 16 install, 51-table schema, pgvector, PgBouncer, backup cron",
     "YELLOW", "30 min",
     "psql, pg_dump, pgvector extension"],
    ["AGENT 3", "API", "FastAPI app: all 13 endpoints, Redis integration, error handling, streaming SSE",
     "YELLOW", "1 hour",
     "Python, FastAPI, uvicorn, redis-py, asyncpg"],
    ["AGENT 4", "STORAGE", "Azure Blob wiring, SAS token generation, upload/download helpers, AI Search indexer",
     "GREEN", "30 min",
     "azure-storage-blob SDK, azure-search SDK"],
    ["AGENT 5", "AI", "Azure OpenAI streaming, embeddings pipeline, vectorization worker, RAG chain",
     "YELLOW", "30 min",
     "openai SDK, tiktoken, asyncio workers"],
    ["AGENT 6", "SECURITY", "NSG rules, fail2ban, SSH hardening, managed identity, secrets management, monitoring",
     "RED", "30 min",
     "Azure CLI, ufw, fail2ban, Azure Monitor"],
]

story.append(make_table(
    ["Agent", "Role", "Scope", "Zone", "Time", "Tools"],
    agent_rows,
    col_widths=[0.6*inch, 0.7*inch, 1.8*inch, 0.5*inch, 0.5*inch, 2.4*inch]
))

story.append(Spacer(1, 12))
story.append(Paragraph("Agent Coordination Protocol", styles['SubHead']))

story.extend(diagram_block([
    "============================================================",
    "  AGENT SWARM COORDINATION",
    "============================================================",
    "",
    "  AGENT 1 (INFRA) ----+",
    "       |               |  Phase 1: VM + OS + Nginx",
    "       v               |  (must complete before others)",
    "  [VM READY]           |",
    "       |               |",
    "       +------+--------+--------+--------+",
    "       |      |        |        |        |",
    "     AG-2   AG-3     AG-4     AG-5     AG-6",
    "     (DB)   (API)   (STOR)   (AI)     (SEC)",
    "       |      |        |        |        |",
    "       v      v        v        v        v",
    "  [Phase 2: All agents run in parallel]",
    "       |      |        |        |        |",
    "       +------+--------+--------+--------+",
    "       |",
    "       v",
    "  [INTEGRATION TEST]",
    "       |",
    "       v",
    "  [DEPLOY TO PRODUCTION]",
    "============================================================",
]))

story.append(Spacer(1, 12))
story.append(Paragraph("Agent Rules (Shared CLAUDE.md)", styles['SubHead']))

story.append(Paragraph(
    "# MENAGERIE VM DEPLOYMENT - AGENT RULES<br/><br/>"
    "## Universal Rules (All Agents)<br/>"
    "- Zone system: RED = human approval, YELLOW = test required, GREEN = autonomy<br/>"
    "- Time blocks: 1/5/10/30/60 min. Over 2 hours = WARNING<br/>"
    "- No hallucinations. Every command must be tested before marking complete<br/>"
    "- Update STATUS.md after each completed step<br/>"
    "- If blocked, write BLOCKED:{reason} to STATUS.md and stop<br/>"
    "- Never modify files owned by another agent<br/>"
    "- All secrets via environment variables, never hardcoded<br/>"
    "- Log every action to /var/log/menagerie/agent-{N}.log<br/>",
    styles['CodeBlock']
))

story.append(PageBreak())

story.append(Paragraph("Agent 1: INFRA — Prompt", styles['SubHead3']))
story.append(Paragraph(
    "You are AGENT-1-INFRA. Your job: provision the Azure VM and configure the OS layer.<br/><br/>"
    "TASKS:<br/>"
    "1. Create resource group 'menagerie-rg' in eastus<br/>"
    "2. Provision D4s_v5 VM with Ubuntu 24.04<br/>"
    "3. Install Nginx, configure HTTP/2 + TLS 1.3 via Certbot<br/>"
    "4. Enable gzip (level 6, json/text/css/js, min 256 bytes)<br/>"
    "5. Configure systemd service template for FastAPI<br/>"
    "6. Set up logrotate (7-day retention, compress)<br/>"
    "7. Configure UFW: allow 443/tcp, allow 22/tcp from ADMIN_IP only<br/>"
    "8. Write nginx.conf to /etc/nginx/sites-available/menagerie<br/>"
    "9. Verify: curl -I https://DOMAIN returns 200 with h2<br/>"
    "10. Update STATUS.md: INFRA=COMPLETE<br/><br/>"
    "DEPENDENCIES: None. You run first.<br/>"
    "TIME TARGET: 30 minutes<br/>"
    "ZONE: GREEN (no production data yet)",
    styles['CodeBlock']
))

story.append(Paragraph("Agent 2: DATABASE — Prompt", styles['SubHead3']))
story.append(Paragraph(
    "You are AGENT-2-DATABASE. Your job: install and configure PostgreSQL 16 with full schema.<br/><br/>"
    "WAIT FOR: STATUS.md shows INFRA=COMPLETE<br/><br/>"
    "TASKS:<br/>"
    "1. Install PostgreSQL 16 + pgvector extension<br/>"
    "2. Create database 'menagerie' and user 'menagerie_app'<br/>"
    "3. Load 51-table schema from schema.sql<br/>"
    "4. Configure postgresql.conf: max_connections=200, shared_buffers=4GB,<br/>"
    "&nbsp;&nbsp;&nbsp;work_mem=64MB, effective_cache_size=12GB<br/>"
    "5. Enable PgBouncer (pool_mode=transaction, max_client_conn=400)<br/>"
    "6. Create backup script: pg_dump -> gzip -> az storage blob upload<br/>"
    "7. Add cron: 0 3 * * * /opt/menagerie/backup.sh<br/>"
    "8. Install Redis 7, configure maxmemory=2gb, allkeys-lru<br/>"
    "9. Create systemd services for PostgreSQL and Redis<br/>"
    "10. Verify: psql -c 'SELECT count(*) FROM information_schema.tables'<br/>"
    "11. Update STATUS.md: DATABASE=COMPLETE<br/><br/>"
    "ZONE: YELLOW (schema changes require review)",
    styles['CodeBlock']
))

story.append(Paragraph("Agent 3: API — Prompt", styles['SubHead3']))
story.append(Paragraph(
    "You are AGENT-3-API. Your job: build the complete FastAPI application.<br/><br/>"
    "WAIT FOR: STATUS.md shows INFRA=COMPLETE<br/><br/>"
    "TASKS:<br/>"
    "1. Create Python 3.12 venv at /opt/menagerie/venv<br/>"
    "2. Install: fastapi uvicorn asyncpg redis aiohttp python-multipart pydantic<br/>"
    "3. Build FastAPI app with 13 endpoints (see endpoint map)<br/>"
    "4. Implement connection pooling: asyncpg pool (min=5, max=20)<br/>"
    "5. Implement Redis caching layer with 5-min TTL for reads<br/>"
    "6. Implement SSE streaming endpoint for /api/chat<br/>"
    "7. Add request validation with Pydantic models<br/>"
    "8. Add structured error responses (JSON, status codes, error codes)<br/>"
    "9. Add request logging middleware (method, path, status, latency_ms)<br/>"
    "10. Create systemd service: menagerie-api.service<br/>"
    "11. Verify: all 13 endpoints return expected responses<br/>"
    "12. Update STATUS.md: API=COMPLETE<br/><br/>"
    "ZONE: YELLOW (core application logic)",
    styles['CodeBlock']
))

story.append(PageBreak())

story.append(Paragraph("Agent 4: STORAGE — Prompt", styles['SubHead3']))
story.append(Paragraph(
    "You are AGENT-4-STORAGE. Your job: wire Azure Blob Storage and AI Search.<br/><br/>"
    "WAIT FOR: STATUS.md shows INFRA=COMPLETE<br/><br/>"
    "TASKS:<br/>"
    "1. Install azure-storage-blob, azure-search-documents SDKs<br/>"
    "2. Create Blob container 'menagerie-uploads' with private access<br/>"
    "3. Build SAS token generator (5-min expiry, write-only, per-blob)<br/>"
    "4. Build upload confirmation handler (save metadata to PG)<br/>"
    "5. Create AI Search index 'menagerie-docs' with schema<br/>"
    "6. Build index push function (document -> AI Search)<br/>"
    "7. Build search query function with filters and facets<br/>"
    "8. Wire storage helpers into FastAPI app (import as module)<br/>"
    "9. Verify: generate SAS token, upload test file, confirm in Blob<br/>"
    "10. Verify: push test doc to AI Search, query returns result<br/>"
    "11. Update STATUS.md: STORAGE=COMPLETE<br/><br/>"
    "ZONE: GREEN (no production data risk)",
    styles['CodeBlock']
))

story.append(Paragraph("Agent 5: AI — Prompt", styles['SubHead3']))
story.append(Paragraph(
    "You are AGENT-5-AI. Your job: wire Azure OpenAI and build the vectorization pipeline.<br/><br/>"
    "WAIT FOR: STATUS.md shows INFRA=COMPLETE<br/><br/>"
    "TASKS:<br/>"
    "1. Install openai, tiktoken SDKs<br/>"
    "2. Build streaming chat endpoint using Azure OpenAI (SSE)<br/>"
    "3. Build embeddings function (text-embedding-3-large, 3072 dims)<br/>"
    "4. Build text chunker (512 tokens, 50 overlap, tiktoken counter)<br/>"
    "5. Build vectorization worker (async): fetch blob -> extract -> chunk -> embed -> store<br/>"
    "6. Store vectors in PostgreSQL pgvector (HNSW index, cosine distance)<br/>"
    "7. Build RAG chain: query -> vector search -> context assembly -> LLM call<br/>"
    "8. Add retry logic with tenacity (3 retries, exponential backoff)<br/>"
    "9. Add fallback: if Azure OpenAI 429, route to Anthropic API<br/>"
    "10. Verify: embed test document, retrieve via similarity search<br/>"
    "11. Verify: chat endpoint streams tokens correctly<br/>"
    "12. Update STATUS.md: AI=COMPLETE<br/><br/>"
    "ZONE: YELLOW (AI pipeline is core functionality)",
    styles['CodeBlock']
))

story.append(Paragraph("Agent 6: SECURITY — Prompt", styles['SubHead3']))
story.append(Paragraph(
    "You are AGENT-6-SECURITY. Your job: harden the VM and set up monitoring.<br/><br/>"
    "WAIT FOR: STATUS.md shows INFRA=COMPLETE<br/><br/>"
    "TASKS:<br/>"
    "1. Configure NSG: 443 open, 22 from ADMIN_IP only, deny all else<br/>"
    "2. Install and configure fail2ban (SSH: 3 attempts, 1hr ban)<br/>"
    "3. Disable password SSH auth, key-only<br/>"
    "4. Set up Azure Managed Identity for VM<br/>"
    "5. Configure DefaultAzureCredential for all SDK calls<br/>"
    "6. Create /opt/menagerie/.env with all secrets, chmod 600<br/>"
    "7. Set up Azure Monitor agent + disk/CPU/memory alerts<br/>"
    "8. Configure UptimeRobot (free) for /api/health endpoint<br/>"
    "9. Set up unattended-upgrades for security patches<br/>"
    "10. Run Lynis security audit, fix any HIGH findings<br/>"
    "11. Verify: nmap scan from external shows only 443 open<br/>"
    "12. Update STATUS.md: SECURITY=COMPLETE<br/><br/>"
    "ZONE: RED (security changes require human review)",
    styles['CodeBlock']
))

story.append(PageBreak())

# ═══════════════════════════════════════════════
# 07 — FULL SETUP SCRIPT
# ═══════════════════════════════════════════════
story.append(Paragraph("07  FULL SETUP SCRIPT", styles['SectionHead']))
story.append(hr())

story.append(Paragraph(
    "Single script. SSH in once. Run it. Walk away for 20 minutes. "
    "Come back to a fully running production server.",
    styles['Body']
))

story.append(Paragraph(
    "#!/bin/bash<br/>"
    "set -euo pipefail<br/>"
    "# ═══════════════════════════════════════════════<br/>"
    "# MENAGERIE VM SETUP - ONE SCRIPT, ONE RUN<br/>"
    "# ═══════════════════════════════════════════════<br/><br/>"
    "DOMAIN='menagerie.yourdomain.com'<br/>"
    "DB_NAME='menagerie'<br/>"
    "DB_USER='menagerie_app'<br/>"
    "DB_PASS='CHANGE_ME_STRONG_PASSWORD'<br/>"
    "ADMIN_EMAIL='alan@digitalprinciples.com'<br/><br/>"
    "echo '=== [1/8] System Update ==='<br/>"
    "sudo apt update &amp;&amp; sudo apt upgrade -y<br/>"
    "sudo apt install -y nginx postgresql-16 postgresql-16-pgvector \\<br/>"
    "&nbsp;&nbsp;redis-server python3.12 python3.12-venv python3-pip \\<br/>"
    "&nbsp;&nbsp;certbot python3-certbot-nginx fail2ban ufw logrotate curl<br/><br/>"
    "echo '=== [2/8] PostgreSQL ==='<br/>"
    "sudo -u postgres psql -c \"CREATE DATABASE $DB_NAME;\"<br/>"
    "sudo -u postgres psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';\"<br/>"
    "sudo -u postgres psql -c \"GRANT ALL ON DATABASE $DB_NAME TO $DB_USER;\"<br/>"
    "sudo -u postgres psql -d $DB_NAME -c 'CREATE EXTENSION IF NOT EXISTS vector;'<br/><br/>"
    "echo '=== [3/8] Redis ==='<br/>"
    "sudo sed -i 's/# maxmemory .*/maxmemory 2gb/' /etc/redis/redis.conf<br/>"
    "sudo sed -i 's/# maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf<br/>"
    "sudo systemctl restart redis<br/><br/>"
    "echo '=== [4/8] Python + FastAPI ==='<br/>"
    "sudo mkdir -p /opt/menagerie<br/>"
    "python3.12 -m venv /opt/menagerie/venv<br/>"
    "source /opt/menagerie/venv/bin/activate<br/>"
    "pip install fastapi uvicorn[standard] asyncpg redis aiohttp \\<br/>"
    "&nbsp;&nbsp;python-multipart pydantic azure-storage-blob \\<br/>"
    "&nbsp;&nbsp;azure-search-documents openai tiktoken tenacity<br/><br/>"
    "echo '=== [5/8] Nginx + TLS ==='<br/>"
    "# (nginx config written separately, see Agent 1)<br/>"
    "sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $ADMIN_EMAIL<br/><br/>"
    "echo '=== [6/8] Firewall ==='<br/>"
    "sudo ufw default deny incoming<br/>"
    "sudo ufw allow 443/tcp<br/>"
    "sudo ufw allow 22/tcp  # restrict to IP in NSG<br/>"
    "sudo ufw --force enable<br/><br/>"
    "echo '=== [7/8] fail2ban ==='<br/>"
    "sudo systemctl enable fail2ban<br/>"
    "sudo systemctl start fail2ban<br/><br/>"
    "echo '=== [8/8] Systemd Services ==='<br/>"
    "# FastAPI service<br/>"
    "cat &lt;&lt;EOF | sudo tee /etc/systemd/system/menagerie-api.service<br/>"
    "[Unit]<br/>"
    "Description=Menagerie FastAPI<br/>"
    "After=network.target postgresql.service redis.service<br/>"
    "[Service]<br/>"
    "Type=exec<br/>"
    "User=alan<br/>"
    "WorkingDirectory=/opt/menagerie<br/>"
    "EnvironmentFile=/opt/menagerie/.env<br/>"
    "ExecStart=/opt/menagerie/venv/bin/uvicorn app.main:app \\<br/>"
    "&nbsp;&nbsp;--host 127.0.0.1 --port 8000 --workers 4<br/>"
    "Restart=always<br/>"
    "RestartSec=3<br/>"
    "[Install]<br/>"
    "WantedBy=multi-user.target<br/>"
    "EOF<br/><br/>"
    "sudo systemctl daemon-reload<br/>"
    "sudo systemctl enable menagerie-api<br/>"
    "sudo systemctl start menagerie-api<br/><br/>"
    "echo '=== SETUP COMPLETE ==='<br/>"
    "echo 'All services running. Verify: curl https://$DOMAIN/api/health'",
    styles['CodeSmall']
))

story.append(PageBreak())

# ═══════════════════════════════════════════════
# 08 — CLAUDE CODE DROP-IN RULES
# ═══════════════════════════════════════════════
story.append(Paragraph("08  CLAUDE CODE DROP-IN RULES", styles['SectionHead']))
story.append(hr())

story.append(Paragraph(
    "Copy this into your CLAUDE.md. It gives Claude Code full context to execute "
    "any task on the Menagerie VM stack.",
    styles['Body']
))

story.append(Paragraph(
    "# MENAGERIE VM - CLAUDE CODE RULES<br/><br/>"
    "## Architecture<br/>"
    "- Single Azure VM: D4s_v5, Ubuntu 24.04, East US<br/>"
    "- Stack: Nginx (HTTP/2) -> FastAPI (uvicorn, 4 workers) -> PostgreSQL 16 + Redis<br/>"
    "- External: Azure Blob (SAS upload), AI Search, Azure OpenAI (streaming)<br/>"
    "- Deploy: SSH -> git pull -> systemctl restart menagerie-api<br/>"
    "- All code lives at /opt/menagerie/<br/><br/>"
    "## File Ownership<br/>"
    "- /etc/nginx/sites-available/menagerie -> AGENT-1 (INFRA)<br/>"
    "- /opt/menagerie/schema.sql -> AGENT-2 (DATABASE)<br/>"
    "- /opt/menagerie/app/ -> AGENT-3 (API)<br/>"
    "- /opt/menagerie/app/storage/ -> AGENT-4 (STORAGE)<br/>"
    "- /opt/menagerie/app/ai/ -> AGENT-5 (AI)<br/>"
    "- /opt/menagerie/.env, firewall, fail2ban -> AGENT-6 (SECURITY)<br/><br/>"
    "## Zone Rules<br/>"
    "- RED: .env, firewall rules, SSL certs, backup scripts -> HUMAN APPROVAL<br/>"
    "- YELLOW: schema changes, API endpoints, AI pipeline -> REQUIRE TESTS<br/>"
    "- GREEN: docs, utilities, new features, monitoring -> FULL AUTONOMY<br/><br/>"
    "## Speed Rules<br/>"
    "- HTTP/2 enabled on Nginx (listen 443 ssl http2)<br/>"
    "- gzip on all JSON responses (level 6, min 256 bytes)<br/>"
    "- Tauri client uses single reqwest::Client with connection pooling<br/>"
    "- Redis caches all reads with 5-min TTL<br/>"
    "- PgBouncer for connection pooling (transaction mode)<br/>"
    "- SAS token direct-to-blob for file uploads<br/>"
    "- SSE streaming for all AI responses<br/><br/>"
    "## Error Prevention<br/>"
    "- All services: systemd Restart=always, RestartSec=3<br/>"
    "- Postgres: max_connections=200, backup cron nightly<br/>"
    "- Redis: maxmemory=2gb, allkeys-lru eviction<br/>"
    "- Nginx: client_max_body_size=10m (files bypass via SAS)<br/>"
    "- SSL: certbot auto-renew cron monthly<br/>"
    "- Monitoring: Azure Monitor + UptimeRobot on /api/health<br/><br/>"
    "## Time Blocks<br/>"
    "- 1 min: config tweak, single query<br/>"
    "- 5 min: add endpoint, fix bug<br/>"
    "- 10 min: new feature, refactor module<br/>"
    "- 30 min: full pipeline, integration<br/>"
    "- 1 hour: major feature, migration<br/>"
    "- >2 hours: WARNING - 'Could fuck your day Alan'<br/><br/>"
    "## Merge Rules (A/B/C/D/E)<br/>"
    "- A: Deployment (faster/safer shipping)<br/>"
    "- B: Revenue (money in)<br/>"
    "- C: Cost (money out reduction)<br/>"
    "- D: Organization (clarity, maintainability)<br/>"
    "- E: Legal (risk reduction, compliance)<br/>",
    styles['CodeSmall']
))

story.append(PageBreak())

# ═══════════════════════════════════════════════
# 09 — COST ANALYSIS
# ═══════════════════════════════════════════════
story.append(Paragraph("09  COST ANALYSIS", styles['SectionHead']))
story.append(hr())

cost_detail_rows = [
    ["Azure VM D4s_v5", "Pay-as-you-go", "$140/mo", "Always on, 4 vCPU, 16GB"],
    ["Azure VM D4s_v5", "1-year reserved", "$85/mo", "39% savings"],
    ["Azure VM D4s_v5", "3-year reserved", "$55/mo", "61% savings"],
    ["Managed Disk (128GB P10)", "Standard", "$20/mo", "OS + app + DB data"],
    ["Azure Blob Storage", "Hot tier", "$10/mo", "~100GB uploads"],
    ["Azure AI Search", "Basic", "$75/mo", "1 replica, 15GB index"],
    ["Azure OpenAI", "Usage", "~$50/mo", "GPT-4o chat + embeddings"],
    ["Domain + DNS", "Azure DNS", "$1/mo", "Zone hosting"],
    ["TLS Certificate", "Let's Encrypt", "$0/mo", "Auto-renew via Certbot"],
    ["Monitoring", "Azure Monitor Basic", "$0/mo", "Included with VM"],
    ["UptimeRobot", "Free tier", "$0/mo", "50 monitors, 5-min checks"],
]

story.append(make_table(
    ["Service", "Tier", "Cost", "Notes"],
    cost_detail_rows,
    col_widths=[1.8*inch, 1.2*inch, 0.8*inch, 2.7*inch]
))

story.append(Spacer(1, 12))

totals_rows = [
    ["Pay-as-you-go", "$296/mo", "$3,552/yr"],
    ["1-year reserved", "$241/mo", "$2,892/yr"],
    ["3-year reserved", "$211/mo", "$2,532/yr"],
]

story.append(make_table(
    ["Pricing Model", "Monthly Total", "Annual Total"],
    totals_rows,
    col_widths=[2.2*inch, 2.2*inch, 2.1*inch],
    header_color=GREEN
))

story.append(PageBreak())

# ═══════════════════════════════════════════════
# 10 — IMPLEMENTATION TIMELINE
# ═══════════════════════════════════════════════
story.append(Paragraph("10  IMPLEMENTATION TIMELINE", styles['SectionHead']))
story.append(hr())

story.append(Paragraph("Phase 1: Foundation (30 min)", styles['SubHead']))
timeline_p1 = [
    ["0:00-0:05", "AGENT 1", "az vm create + SSH key setup", "95%"],
    ["0:05-0:15", "AGENT 1", "apt install all packages", "98%"],
    ["0:15-0:25", "AGENT 1", "Nginx config + Certbot TLS", "90%"],
    ["0:25-0:30", "AGENT 1", "Verify HTTPS + HTTP/2 working", "95%"],
]
story.append(make_table(
    ["Time", "Agent", "Task", "Completion %"],
    timeline_p1,
    col_widths=[0.8*inch, 0.8*inch, 3.6*inch, 1.3*inch]
))

story.append(Spacer(1, 8))
story.append(Paragraph("Phase 2: Parallel Build (1 hour)", styles['SubHead']))
timeline_p2 = [
    ["0:30-0:45", "AGENT 2", "PostgreSQL + pgvector + schema load", "90%"],
    ["0:30-0:45", "AGENT 6", "Firewall + fail2ban + SSH hardening", "95%"],
    ["0:30-1:00", "AGENT 3", "FastAPI app (13 endpoints)", "85%"],
    ["0:45-1:00", "AGENT 2", "Redis + PgBouncer + backup cron", "90%"],
    ["0:45-1:15", "AGENT 4", "Blob wiring + SAS + AI Search index", "85%"],
    ["0:45-1:15", "AGENT 5", "OpenAI streaming + embeddings + RAG", "80%"],
    ["1:00-1:15", "AGENT 6", "Managed identity + monitoring + alerts", "85%"],
    ["1:15-1:30", "AGENT 3", "Integration with AG-4 and AG-5 modules", "80%"],
]
story.append(make_table(
    ["Time", "Agent", "Task", "Completion %"],
    timeline_p2,
    col_widths=[0.8*inch, 0.8*inch, 3.6*inch, 1.3*inch]
))

story.append(Spacer(1, 8))
story.append(Paragraph("Phase 3: Integration + Verification (30 min)", styles['SubHead']))
timeline_p3 = [
    ["1:30-1:45", "ALL", "End-to-end test: upload -> vectorize -> search -> chat", "85%"],
    ["1:45-1:55", "AGENT 1", "systemd enable all, reboot test, verify auto-start", "95%"],
    ["1:55-2:00", "AGENT 6", "Final security audit (Lynis), nmap verification", "90%"],
]
story.append(make_table(
    ["Time", "Agent", "Task", "Completion %"],
    timeline_p3,
    col_widths=[0.8*inch, 0.8*inch, 3.6*inch, 1.3*inch]
))

story.append(Spacer(1, 12))
story.append(Paragraph(
    "TOTAL WALL CLOCK: 2 HOURS. Overall completion probability: 85%. "
    "Primary risk: Azure networking config (VNet, NSG rules, managed identity). "
    "Mitigation: Agent 6 handles all networking in parallel while other agents build.",
    styles['Warning']
))

story.append(Spacer(1, 12))
story.append(Paragraph(
    "POST-DEPLOY VERIFICATION CHECKLIST: "
    "curl /api/health returns 200. "
    "Upload test file via SAS, confirm in Blob. "
    "CRUD create/read/update/delete on test table. "
    "Chat endpoint streams tokens via SSE. "
    "Reboot VM, all services auto-restart. "
    "nmap shows only port 443 open. "
    "pg_dump backup completes and uploads to Blob.",
    styles['Success']
))

# ─── BUILD ───
doc.build(story)
print("PDF built successfully.")
