#!/bin/bash
set -euo pipefail
# ══════════════════════════════════════════════════════
# MENAGERIE VM SETUP -- SINGLE RUN PROVISIONER
# Edit variables below before running.
# ══════════════════════════════════════════════════════

DOMAIN='menagerie.yourdomain.com'
DB_NAME='menagerie'
DB_USER='menagerie_app'
DB_PASS='CHANGE_ME_STRONG_PASSWORD_HERE'
ADMIN_EMAIL='alan@digitalprinciples.com'
BLOB_ACCOUNT='menageriesa36965'

#── [1/8] SYSTEM ──
echo '=== [1/8] System Update ==='
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx postgresql-16 postgresql-16-pgvector \
  redis-server python3.12 python3.12-venv python3-pip \
  certbot python3-certbot-nginx fail2ban ufw logrotate curl

#── [2/8] POSTGRESQL ──
echo '=== [2/8] PostgreSQL ==='
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
sudo -u postgres psql -c "GRANT ALL ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -d $DB_NAME -c 'CREATE EXTENSION IF NOT EXISTS vector;'
# Tune postgresql.conf
sudo sed -i "s/#shared_buffers.*/shared_buffers = '4GB'/" /etc/postgresql/16/main/postgresql.conf
sudo sed -i "s/#work_mem.*/work_mem = '64MB'/" /etc/postgresql/16/main/postgresql.conf
sudo sed -i "s/#effective_cache_size.*/effective_cache_size = '12GB'/" /etc/postgresql/16/main/postgresql.conf
sudo sed -i "s/max_connections.*/max_connections = 200/" /etc/postgresql/16/main/postgresql.conf
sudo systemctl restart postgresql

#── [3/8] REDIS ──
echo '=== [3/8] Redis ==='
sudo sed -i 's/# maxmemory .*/maxmemory 2gb/' /etc/redis/redis.conf
sudo sed -i 's/# maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
sudo systemctl restart redis

#── [4/8] PYTHON + FASTAPI ──
echo '=== [4/8] Python + FastAPI ==='
sudo mkdir -p /opt/menagerie/app/{routes,models,middleware,storage,ai}
python3.12 -m venv /opt/menagerie/venv
source /opt/menagerie/venv/bin/activate
pip install fastapi 'uvicorn[standard]' asyncpg redis aiohttp \
  python-multipart pydantic azure-storage-blob \
  azure-search-documents openai tiktoken tenacity \
  azure-identity python-dotenv

#── [5/8] NGINX + TLS ──
echo '=== [5/8] Nginx + TLS ==='
cat <<'NGINX' | sudo tee /etc/nginx/sites-available/menagerie
server {
  listen 443 ssl http2;
  server_name DOMAIN_PLACEHOLDER;

  ssl_protocols TLSv1.3;
  ssl_prefer_server_ciphers off;

  gzip on;
  gzip_vary on;
  gzip_proxied any;
  gzip_comp_level 6;
  gzip_min_length 256;
  gzip_types application/json text/plain text/css application/javascript;

  client_max_body_size 10m;

  location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_buffering off;  # Required for SSE streaming
  }
}
NGINX

# Replace domain placeholder
sudo sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/" /etc/nginx/sites-available/menagerie
sudo ln -sf /etc/nginx/sites-available/menagerie /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $ADMIN_EMAIL
sudo systemctl reload nginx

#── [6/8] FIREWALL ──
echo '=== [6/8] Firewall ==='
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # Restrict to IP via Azure NSG
sudo ufw --force enable

#── [7/8] FAIL2BAN + SSH HARDENING ──
echo '=== [7/8] Security ==='
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
sudo systemctl enable fail2ban && sudo systemctl start fail2ban

#── [8/8] SYSTEMD + BACKUP ──
echo '=== [8/8] Services ==='
cat <<'SVC' | sudo tee /etc/systemd/system/menagerie-api.service
[Unit]
Description=Menagerie FastAPI
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=alan
WorkingDirectory=/opt/menagerie
EnvironmentFile=/opt/menagerie/.env
ExecStart=/opt/menagerie/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SVC

# Backup cron
cat <<'BACKUP' | sudo tee /opt/menagerie/backup.sh
#!/bin/bash
pg_dump menagerie | gzip > /tmp/menagerie-$(date +%Y%m%d).sql.gz
az storage blob upload --account-name menageriesa36965 --container-name backups \
  --file /tmp/menagerie-$(date +%Y%m%d).sql.gz --name db/$(date +%Y%m%d).sql.gz --auth-mode login
rm /tmp/menagerie-*.sql.gz
BACKUP
chmod +x /opt/menagerie/backup.sh
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/menagerie/backup.sh") | crontab -

sudo systemctl daemon-reload
sudo systemctl enable menagerie-api
sudo systemctl start menagerie-api

echo '══════════════════════════════════════════'
echo '  MENAGERIE VM SETUP COMPLETE'
echo "  Verify: curl https://$DOMAIN/api/health"
echo '══════════════════════════════════════════'
