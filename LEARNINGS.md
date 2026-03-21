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
| NocoDB | `data.bjblabs.com` | Docker → port 8080 |

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
- **Zero Trust:** Enabled (Free plan, `bjblabs.cloudflareaccess.com`). See `docs/zero-trust-setup.md`.

## Anki Renderer (LIVE)

- Static Vite demo served by Caddy from `~/services/anki-renderer/dist/`
- **CI/CD:** push → GitHub Actions → tarball POST to webhook → extracted to dist/
- **Webhook:** `~/services/anki-renderer/deploy-webhook.py` (port 9001, launchd managed)
- **Secret:** `~/services/anki-renderer/.deploy-secret` + `DEPLOY_WEBHOOK_SECRET` GitHub secret

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
- **Email:** Resend (`bjblabs.com` domain verified, API key configured in `.env`)
- **Pending:** LegalPodcastStack deletion (#62) — needs 1+ weeks stability + Ben's approval

## NocoDB (LIVE — local only, pending DNS/Zero Trust)

- **Directory:** `~/services/nocodb/` (compose, .env, data)
- **Start:** `cd ~/services/nocodb && docker compose up -d`
- **Port:** 8080 (NocoDB admin UI)
- **Data:** SQLite at `~/services/nocodb/data/noco.db`
- **Secrets:** `.env` file (chmod 600) — `NC_AUTH_JWT_SECRET`
- **DNS:** CNAME `data.bjblabs.com` → tunnel (Cloudflare record ID: `01a081695d60c0e228d602a967d02f7c`)
- **Zero Trust:** Access app `c1b4abb1-0184-4e6b-b812-2b226dc41921`, Allow policy for Ben + Service Token `NocoDB MCP`
- **Service Token creds:** `~/services/nocodb/.cf-service-token` (CF_ACCESS_CLIENT_ID + CF_ACCESS_CLIENT_SECRET)
- **Pending:** Data migration (#17), backups (#18)

## Monitoring & Backups

- **Telegram bot:** `@ben_mac_mini_alerts_bot`, creds: `~/services/config/alerts/telegram.env`
- **Health checks:** `~/services/scripts/health-check.sh` (10 checks), launchd every 5 min, Telegram alerts
- **Backups:** `~/services/scripts/backup.sh`, launchd daily 3am, 7-day local + 4-week weekly + S3 off-site
- **S3 bucket:** `s3://bjblabs-backups-719390918663/mac-mini/` (IAM: `mac-mini-backup`)
- **Restore docs:** `~/services/config/restore-procedure.md`
- **Docker Desktop:** Start via SSH: `nohup /Applications/Docker.app/Contents/MacOS/com.docker.backend --start-docker-desktop > /dev/null 2>&1 &`

## Gotchas

- SSH sessions have minimal PATH — `~/.zshenv` adds `/usr/local/bin` and `/opt/homebrew/bin`
- Docker `credsStore: desktop` fails in SSH (keychain locked) — removed from config.json
- Docker Desktop won't start via `open -a Docker` over SSH — use `com.docker.backend` command
- cloudflared arg order: `tunnel --config <path> run` (--config before run)
- `launchctl` fails via SSH (exit 134) — use `nohup` over SSH; LaunchAgents work on GUI login/reboot
- Docker bridge: 127.0.0.1 inside container unreachable via port mapping — bind 0.0.0.0
- OpenClaw sandbox-browser needs `OPENCLAW_BROWSER_NO_SANDBOX: "1"` + custom CDP proxy
- OpenClaw non-loopback: set `controlUi.dangerouslyAllowHostHeaderOriginFallback: true`
- SSH command expansion: `$(cmd)` in double-quoted `ssh mac-mini "..."` expands locally — use single quotes
- Caddy + launchd: NEVER `caddy start`/`caddy stop` over SSH — launchd (KeepAlive) spawns duplicates. Use `killall caddy` and let launchd restart.

## Repo Conventions

- Work tracked via GitHub Issues (`migration` label), sequential numbering
- Direct commits to `main`, messages reference issues: `feat: ... Part of #N`
- HANDOFF.md is gitignored — transient for human-agent handoffs
- Docs deployed to both `docs/` (repo) and `~/services/config/` (Mac Mini)
