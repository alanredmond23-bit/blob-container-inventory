# MENAGERIE VM -- CLAUDE CODE EXECUTION RULES

## Architecture
- Single Azure VM: D4s_v5 (4 vCPU, 16GB), Ubuntu 24.04, East US
- Stack: Nginx (HTTP/2, TLS 1.3, gzip) -> FastAPI (uvicorn, 4 workers) -> PostgreSQL 16 + Redis 7
- External services: Azure Blob (menageriesa36965), AI Search (menagerie-search-37161), Azure OpenAI
- Frontend: Tauri desktop app, connects via HTTPS REST only, SSE for AI streaming
- Deploy: ssh alan@vm -> cd /opt/menagerie -> git pull -> systemctl restart menagerie-api

## File Layout
- /opt/menagerie/app/main.py -- FastAPI app entry
- /opt/menagerie/app/routes/ -- endpoint routers
- /opt/menagerie/app/models/ -- Pydantic schemas
- /opt/menagerie/app/storage/ -- Blob + AI Search helpers
- /opt/menagerie/app/ai/ -- OpenAI + embeddings + RAG
- /opt/menagerie/app/middleware/ -- logging, error handling
- /opt/menagerie/.env -- all secrets (chmod 600)
- /opt/menagerie/schema.sql -- PostgreSQL schema
- /etc/nginx/sites-available/menagerie -- Nginx config

## Zone Rules
- RED: .env, firewall, SSL certs, backup scripts, DELETE endpoints -> HUMAN APPROVAL
- YELLOW: schema changes, API endpoints, AI pipeline, PgBouncer config -> REQUIRE TESTS
- GREEN: docs, utilities, new features, monitoring, GET endpoints -> FULL AUTONOMY

## Speed Rules (non-negotiable)
- HTTP/2 on Nginx: listen 443 ssl http2
- gzip on all JSON: level 6, min 256 bytes
- Tauri: single reqwest::Client with http2_prior_knowledge + pool_max_idle=10 + keepalive=60s
- Redis: cache all reads, 5-min TTL, sub-1ms localhost
- PgBouncer: transaction mode, max 400 client connections
- File uploads: SAS token direct-to-blob, never route bytes through VM
- AI responses: SSE streaming, never buffer full response
- Nginx: proxy_buffering off for SSE endpoints

## Error Prevention (baked in)
- All systemd services: Restart=always, RestartSec=3
- Postgres: max_connections=200, nightly pg_dump to Blob
- Redis: maxmemory=2gb, allkeys-lru eviction
- Nginx: client_max_body_size=10m (files bypass via SAS)
- SSL: certbot auto-renew cron monthly
- SSH: key-only, fail2ban, NSG restricts to admin IP
- Monitoring: Azure Monitor alerts + UptimeRobot /api/health

## Time Blocks
- 1 min: config tweak, single-line fix, quick lookup
- 5 min: add endpoint, fix bug, add test
- 10 min: new feature scaffold, refactor module
- 30 min: full pipeline, integration work
- 1 hour: major feature, complex migration
- >2 hours: WARNING -- 'Could fuck your day Alan'

## Merge Rules (every change serves one)
- A: Deployment (faster/safer shipping)
- B: Revenue (money in)
- C: Cost (money out reduction)
- D: Organization (clarity, maintainability)
- E: Legal (risk reduction, compliance)

## Elon Algorithm (apply to EVERY request)
1. Make Requirements Less Dumb -- do we actually need this?
2. Delete the Part or Process -- can we remove this?
3. Simplify or Optimize -- NEVER optimize what shouldn't exist
4. Accelerate Cycle Time -- speed of iteration > speed of runtime
5. Automate Last -- only automate boring, stable, repetitive work

## Key Azure Resources
- Storage account: menageriesa36965
- Key Vault: menagerie-kv-37040
- AI Search: menagerie-search-37161
- SQL DB: menagerie-sql
- Supabase (legacy relational): fifybuzwfaegloijrmqb
- Azure subscription: 0ea4eea5

## 6-Agent Swarm (for major deployments)
- AG-1 INFRA: VM, Nginx, systemd, TLS, firewall (runs first, sequential gate)
- AG-2 DATABASE: PostgreSQL, pgvector, PgBouncer, Redis, backup cron
- AG-3 API: FastAPI 13 endpoints, Redis cache, SSE streaming, Pydantic
- AG-4 STORAGE: Azure Blob SAS, AI Search index, upload/download helpers
- AG-5 AI: Azure OpenAI streaming, embeddings, chunker, vectorization, RAG
- AG-6 SECURITY: NSG, fail2ban, SSH, managed identity, monitoring, Lynis
- Coordination: STATUS.md file, agents 2-6 parallel after agent 1 completes

## Endpoint Map (13 routes)
- POST /api/auth/token -- JWT issuance
- GET  /api/health -- health check
- POST /api/crud/{table} -- create
- GET  /api/crud/{table}/{id} -- read
- PUT  /api/crud/{table}/{id} -- update
- DELETE /api/crud/{table}/{id} -- delete (RED zone)
- POST /api/upload/sas -- SAS token generation
- POST /api/upload/confirm -- confirm upload + trigger vectorize
- POST /api/search -- AI Search query
- POST /api/chat -- AI chat (SSE streaming)
- GET  /api/vectors/{doc_id} -- get embeddings
- POST /api/batch/vectorize -- batch vectorize (async)
- GET  /api/jobs/{job_id} -- check async job status
