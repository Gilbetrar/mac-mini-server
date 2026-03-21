# LEARNINGS.md — Mac Mini Server

Distilled patterns for autonomous agents. Keep under 100 lines.

## Project Overview

Migration of services from AWS to self-hosted M4 Mac Mini.
SSH: `ssh mac-mini`, user: `ben`, home: `/Users/ben`, sudo available.
Services root: `~/services/` (subdirs: `config/`, `data/`, `backups/`)

## Service Routing

Internet → Cloudflare CNAME (proxied) → cloudflared tunnel → Caddy (:80) → service
- cloudflared: single catch-all ingress → Caddy handles host routing
- **Add new service:** (1) Caddy host route, (2) Cloudflare CNAME DNS record

| Service | URL | Backend |
|---------|-----|---------|
| Anki Renderer | `anki-renderer.bjblabs.com` | Caddy file_server → `~/services/anki-renderer/dist/` |
| Deploy webhook | `anki-renderer.bjblabs.com/_deploy` | Python webhook → port 9001 |
| OpenClaw | `openclaw.bjblabs.com` | Docker gateway → port 18789 |
| Gmail webhook | `openclaw.bjblabs.com/gmail-pubsub` | gog serve → port 8788 (GCP: `vast-nectar-487617-j6`, sub: `gog-gmail-watch-push`) |
| Legal Podcast | `legalpodcast.bjblabs.com` | Docker service → port 9002, static data via Caddy |
| Legal Podcast admin | `legalpodcast.bjblabs.com/` | Caddy file_server → `~/services/legal-podcast/admin-ui/` |

## Caddy

- Binary: `/opt/homebrew/bin/caddy`, Config: `~/services/config/Caddyfile` (version-controlled in `config/`)
- Reload: `caddy reload --config ~/services/config/Caddyfile`
- launchd: `~/Library/LaunchAgents/com.caddy.server.plist`

## Cloudflare

- **Tunnel:** `mac-mini` / `e4978b52-8394-4f5b-b715-ee96a5a9e641`, config: `~/services/config/cloudflared/config.yml`
- **API token:** `~/services/config/.cloudflare-token` (perms: Tunnel, Access, Email Routing Rules, Zone, DNS, Workers Scripts)
- **Zone:** `9d3c311fe7bd41ecab3830a57a3a51a6`, **Account:** `95f53250a929e155644f51e03fc7c910`
- **DNS:** Cloudflare nameservers active since 2026-03-17. Route 53 zone kept as rollback until 2026-03-31.
- **Email Routing:** LIVE — `podcast@` → email worker, catch-all → Gmail. Verify: `dig MX bjblabs.com +short`
- **Email Worker:** `legal-podcast-email-forwarder`, source: `email-worker/`, deploy: `cd email-worker && npx wrangler deploy`
- **Zero Trust:** NOT enabled, requires dashboard. Not blocking other work.

## Anki Renderer (LIVE)

- Static Vite demo served by Caddy from `~/services/anki-renderer/dist/`
- **CI/CD:** push → GitHub Actions → tarball POST to webhook → extracted to dist/
- **Webhook:** `~/services/anki-renderer/deploy-webhook.py` (port 9001, launchd managed)
- **Secret:** `~/services/anki-renderer/.deploy-secret` + `DEPLOY_WEBHOOK_SECRET` GitHub secret
- AWS stack `AnkiRendererDemoStack` deleted 2026-03-20

## OpenClaw (LIVE)

- **Version:** v2026.3.12 (pinned — HEAD has plugin validation regression)
- **Directory:** `~/services/openclaw/` (compose, .env, .openclaw, repo, sandbox-browser-custom)
- **Start:** `cd ~/services/openclaw && docker compose up -d`
- **gog binary:** v0.12.0 ARM64 Linux, mounted from `~/services/openclaw/bin/gog`
- **Claude auth:** `auth-profiles.json` (not env vars). Opus default, Sonnet/Haiku fallbacks.
- **EC2:** `i-0cc417431630fdfc5` STOPPED. Decommission after 2026-03-25 (issue #36).

## Legal Podcast (LIVE)

- **Directory:** `~/services/legal-podcast/` (compose, .env, repo, data, admin-ui)
- **Start:** `cd ~/services/legal-podcast && docker compose up -d`
- **Rebuild:** `cd ~/services/legal-podcast && git -C repo pull && docker compose up -d --build`
- **Port:** 9002 (Express API + webhook)
- **Data:** `~/services/legal-podcast/data/` (bind-mounted to `/data` in container) — migrated from S3 (29 files, 146 MB)
- **Admin UI:** `~/services/legal-podcast/admin-ui/` (served by Caddy, no build step)
- **Secrets:** `.env` file (chmod 600), sourced from AWS SSM `/legal-podcast/*`
- **Email webhook:** Cloudflare Email Worker → `POST /webhooks/email` with `X-Webhook-Secret` header
- **DNS:** CNAME → Cloudflare tunnel (switched from CloudFront)
- **Missing:** RESEND_API_KEY (email notifications won't send until configured)
- **Pending:** LegalPodcastStack deletion (#62) — needs 1+ weeks stability + Ben's approval

## Docker Desktop

- Settings: `~/Library/Group Containers/group.com.docker/settings-store.json` (4 CPUs, 8GB RAM)
- Start headlessly via SSH: `nohup /Applications/Docker.app/Contents/MacOS/com.docker.backend --start-docker-desktop > /dev/null 2>&1 &`

## Telegram Alerts

- Bot: `@ben_mac_mini_alerts_bot`, creds: `~/services/config/alerts/telegram.env` (chmod 600)

## Health Checks (LIVE)

- **Script:** `~/services/scripts/health-check.sh` — checks 10 services
- **Schedule:** launchd `com.bjblabs.healthcheck`, every 5 minutes
- **Alerts:** Telegram on failure, recovery notifications, idempotent (state files in `~/services/data/health-check/`)
- **Logs:** `~/services/data/health-check/health-check.log` (auto-trimmed at 10k lines)
- **Checks:** caddy process, cloudflared process, caddy HTTP, anki-renderer, openclaw-gateway, openclaw-docker, legal-podcast, legal-podcast-docker, deploy-webhook, cloudflare-tunnel (external)

## Backups (LIVE)

- **Script:** `~/services/scripts/backup.sh` — daily tarball of config/ + data/
- **Schedule:** launchd `com.bjblabs.backup`, daily at 3am
- **Local:** `~/services/backups/daily/` (7-day retention), `~/services/backups/weekly/` (4-week, Sundays)
- **Off-site:** `s3://bjblabs-backups-719390918663/mac-mini/` (IAM user: `mac-mini-backup`, scoped to bucket)
- **Restore docs:** `~/services/config/restore-procedure.md`
- **Logs:** `~/services/backups/backup.log` (auto-trimmed at 5k lines)
- Telegram alert on backup failure; idempotent (skips if today's backup exists)

## Gotchas

- `systemsetup` emits `Error:-99` on modern macOS — cosmetic, settings apply
- SSH sessions have minimal PATH — `~/.zshenv` adds `/usr/local/bin` and `/opt/homebrew/bin`
- Docker `credsStore: desktop` fails in SSH (keychain locked) — removed from config.json
- Docker Desktop won't start via `open -a Docker` over SSH — use `com.docker.backend` command
- cloudflared arg order: `tunnel --config <path> run` (--config before run)
- `launchctl` fails via SSH (exit 134) — use `nohup` over SSH; LaunchAgents work on GUI login/reboot
- Docker bridge: 127.0.0.1 inside container unreachable via port mapping — bind 0.0.0.0
- OpenClaw sandbox-browser needs `OPENCLAW_BROWSER_NO_SANDBOX: "1"` + custom CDP proxy
- OpenClaw non-loopback: set `controlUi.dangerouslyAllowHostHeaderOriginFallback: true`
- SSH command expansion: `$(cmd)` in double-quoted `ssh mac-mini "..."` expands locally — use single quotes for remote expansion
- Caddy reload with launchd: NEVER use `caddy start`/`caddy stop` over SSH — launchd (KeepAlive) will spawn duplicates. Instead `killall caddy` and let launchd restart with the updated Caddyfile on disk.

## Repo Conventions

- Work tracked via GitHub Issues (`migration` label), sequential numbering
- Direct commits to `main`, messages reference issues: `feat: ... Part of #N`
- HANDOFF.md is gitignored — transient for human-agent handoffs
- Docs deployed to both `docs/` (repo) and `~/services/config/` (Mac Mini)
