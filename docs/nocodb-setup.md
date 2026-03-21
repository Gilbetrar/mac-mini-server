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

## Pending Work

- **Data migration (#17):** Import Airtable bases (Contacts, Readings, EA Jobs)
- **MCP server (#19):** Configure NocoDB MCP for Claude Code access
- **Documentation (#20):** Agent skills and full documentation update
