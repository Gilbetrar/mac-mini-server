# NocoDB Setup — data.bjblabs.com

## Overview

Self-hosted NocoDB instance replacing Airtable. Runs as a Docker container on the Mac Mini, accessible at `data.bjblabs.com` behind Cloudflare Zero Trust.

**Status:** Infrastructure live (2026-03-21). Data migration pending (#17).

## Architecture

```
Browser/API → Cloudflare DNS (proxied CNAME) → Zero Trust auth → cloudflared tunnel → Caddy → localhost:8080 → NocoDB container
```

## Service Details

| Property | Value |
|----------|-------|
| URL | `https://data.bjblabs.com` |
| Directory | `~/services/nocodb/` on Mac Mini |
| Docker image | `nocodb/nocodb:latest` |
| Port | 8080 |
| Data | SQLite at `~/services/nocodb/data/noco.db` |
| Version | 0.301.5 |
| Compose file | `~/services/nocodb/docker-compose.yml` (template in repo: `services/nocodb/docker-compose.yml`) |

## Access Control

NocoDB is protected by Cloudflare Zero Trust:

| Property | Value |
|----------|-------|
| Access App ID | `c1b4abb1-0184-4e6b-b812-2b226dc41921` |
| Auth method | Email OTP (Ben's email) |
| Service Token | `NocoDB MCP` for programmatic access |
| Service Token creds | `~/services/nocodb/.cf-service-token` |

### Programmatic Access (Service Token)

To access NocoDB API through Zero Trust, include CF service token headers:

```bash
source ~/services/nocodb/.cf-service-token
curl -H "CF-Access-Client-Id: $CF_ACCESS_CLIENT_ID" \
     -H "CF-Access-Client-Secret: $CF_ACCESS_CLIENT_SECRET" \
     https://data.bjblabs.com/api/v1/health
```

### Local Access (from Mac Mini)

```bash
curl http://localhost:8080/api/v1/health
```

## Common Operations

```bash
# Start
cd ~/services/nocodb && docker compose up -d

# Stop
cd ~/services/nocodb && docker compose down

# View logs
cd ~/services/nocodb && docker compose logs -f

# Check version
curl -s http://localhost:8080/api/v1/version

# Check health
curl -s http://localhost:8080/api/v1/health
```

## Environment Variables

| Variable | Purpose | Location |
|----------|---------|----------|
| `NC_AUTH_JWT_SECRET` | JWT signing secret | `~/services/nocodb/.env` |
| `NC_PUBLIC_URL` | Public URL for links/emails | Set in docker-compose.yml |

## DNS

Cloudflare CNAME record `data.bjblabs.com` → tunnel (record ID: `01a081695d60c0e228d602a967d02f7c`).

## Backups

Included in the daily backup script (`~/services/scripts/backup.sh`):
- NocoDB SQLite database (`~/services/nocodb/data/`)
- Local retention: 7 daily + 4 weekly
- Off-site: S3 bucket `s3://bjblabs-backups-719390918663/mac-mini/`

## Monitoring

Health checks run every 5 minutes via `~/services/scripts/health-check.sh`:
- `nocodb-docker`: Docker container running
- `nocodb-http`: HTTP health endpoint responsive

Failures alert via Telegram bot.

## Authentication

| Property | Value |
|----------|-------|
| Admin email | `ben@bjblabs.com` |
| Password | Stored in `~/services/nocodb/.admin-creds` (chmod 600) |
| JWT token | `~/services/nocodb/.api-token` (refresh via sign-in API) |

### API Authentication

```bash
# Get fresh auth token
PASS=$(cat ~/services/nocodb/.admin-creds | grep Password | cut -d" " -f4)
TOKEN=$(curl -s localhost:8080/api/v1/auth/user/signin \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"ben@bjblabs.com\", \"password\": \"$PASS\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
echo "$TOKEN" > ~/services/nocodb/.api-token
```

### API Endpoints

```bash
# List bases in workspace
curl -s "localhost:8080/api/v2/meta/workspaces/wqn2mxm7/bases" -H "xc-auth: $TOKEN"

# List records
curl -s "localhost:8080/api/v1/db/data/noco/{baseId}/{tableId}" -H "xc-auth: $TOKEN"

# Bulk insert records
curl -s -X POST "localhost:8080/api/v1/db/data/bulk/noco/{baseId}/{tableId}" \
  -H "xc-auth: $TOKEN" -H "Content-Type: application/json" -d '[{...}]'
```

## Imported Bases

| Base | NocoDB ID | Tables | Records | Status |
|------|-----------|--------|---------|--------|
| Ben Readings & Notes | `pz0snc66hf3yi5f` | Readings | 746 | Migrated (excl. attachments) |
| Contacts | `p4b83cic6kiud9b` | (empty) | — | Base created, tables pending |
| EA Jobs Database | — | — | — | Blocked by ea-jobs-database#8 |

**Migration notes:**
- Attachments (Anki Cards field) were skipped — too complex for API migration
- Formula fields cannot be imported — must be recreated manually
- Migration script: `scripts/migrate-readings.py`

## Pending Work

- **Data migration (#17):** Contacts base tables + data import remaining. EA Jobs blocked by ea-jobs-database#8.
- **MCP server (#19):** Configure NocoDB MCP for Claude Code access (blocked by #17)
- **Documentation (#20):** Agent skills and full documentation update (blocked by #17 and #19)
