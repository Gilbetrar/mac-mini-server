# EC2 Export Manifest — OpenClaw

## Export Details

| Item | Value |
|------|-------|
| Source | EC2 instance via `ssh ubuntu@100.90.248.10` (Tailscale) |
| Export date | 2026-03-18 |
| Tarball | `~/services/data/openclaw-export.tar.gz` (on Mac Mini) |
| Size | ~291 MB |
| File count (.openclaw) | ~2,404 files |

## Contents

### ~/.openclaw/ (config + data)

| Path | Purpose |
|------|---------|
| `openclaw.json` | Main config (channels, auth, hooks, agents, tools) |
| `openclaw.json.bak*` | Config backups from previous changes |
| `agents/` | Agent state data |
| `browser/` | Browser profile data (Chromium user-data) |
| `canvas/` | Canvas data |
| `completions/` | Completion history |
| `credentials/` | Auth credentials (sensitive) |
| `cron/` | Scheduled task state |
| `delivery-queue/` | Message delivery queue |
| `devices/` | Registered devices |
| `gcloud/` | GCP credentials for Gmail Pub/Sub |
| `identity/` | Identity config |
| `logs/` | Application logs |
| `media/` | Media files |
| `memory/` | Memory/knowledge base |
| `.playwright-browsers/` | Playwright browser binaries (~250 MB) |
| `sandboxes/` | Sandbox configs |
| `subagents/` | Subagent state |
| `telegram/` | Telegram channel state |
| `workspace/` | Agent workspace directory |

### ~/openclaw/ (deployment files)

| File | Purpose |
|------|---------|
| `.env` | Environment variables (see environment-variables.md) |
| `docker-compose.yml` | Container orchestration (3 services) |
| `docker-compose.yml.pre-browser` | Pre-browser-support compose backup |
| `Dockerfile` | Main openclaw image build |
| `Dockerfile.sandbox` | Sandbox container build |
| `Dockerfile.sandbox-browser` | Browser sandbox build |
| `Dockerfile.sandbox-common` | Shared sandbox base |
| `docker-setup.sh` | Setup script |

### ~/.config/gogcli/ (Google integration)

| Path | Purpose |
|------|---------|
| `credentials.json` | Google OAuth credentials |
| `keyring/` | GOG keyring data |
| `drive-downloads/` | Drive download cache |
| `state/` | gogcli state |

## Docker Images

| Image | Tag | Notes |
|-------|-----|-------|
| `openclaw` | `local` | Built from Dockerfile in ~/openclaw/ |
| `openclaw-sandbox-browser` | `bookworm-slim` | Built from Dockerfile.sandbox-browser |

**Note:** These are locally built images, not pulled from a registry. They will need to be rebuilt on the Mac Mini (ARM64 architecture — different from EC2's x86_64).

## Running Services (at export time)

| Container | Image | Ports |
|-----------|-------|-------|
| `openclaw-openclaw-gateway-1` | `openclaw:local` | 8788, 18789-18790 |
| `openclaw-openclaw-sandbox-browser-1` | `openclaw-sandbox-browser:bookworm-slim` | 5900, 6080, 9222 (internal) |

## Verification

```bash
# Verify tarball on Mac Mini
ssh mac-mini "tar tzf ~/services/data/openclaw-export.tar.gz | head -20"

# Extract (when ready)
ssh mac-mini "cd ~/services/data && tar xzf openclaw-export.tar.gz"
```
