# LEARNINGS.md — Mac Mini Server

Distilled patterns for autonomous agents. Keep under 100 lines.

## Project Overview

This repo manages the migration of Ben's services from AWS to a self-hosted M4 Mac Mini.
The Mac Mini is on the local network, accessible via `ssh mac-mini`.

## SSH Access

- **Host alias:** `ssh mac-mini` (configured in `~/.ssh/config` on Ben's laptop)
- **Remote user:** `ben` (home dir: `/Users/ben`)
- **Sudo:** available, use for system commands (`systemsetup`, `pmset`, `socketfilterfw`)

## Directory Structure (on Mac Mini)

- `~/services/` — root for all hosted services
- `~/services/config/` — service configuration files
- `~/services/data/` — persistent service data
- `~/services/backups/` — backup files

## macOS System Settings Applied

- Sleep disabled: `sudo systemsetup -setcomputersleep Never` + `sudo pmset -a displaysleep 0 sleep 0 disksleep 0`
- Auto-restart after power failure: `sudo systemsetup -setrestartpowerfailure on`
- Firewall enabled: `sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on`

## Docker Desktop

- Installed at `/Applications/Docker.app`, CLI symlinks in `/usr/local/bin/`
- Settings file: `~/Library/Group Containers/group.com.docker/settings-store.json`
- Daemon config: `~/.docker/daemon.json` (log rotation configured)
- Resource limits: 4 CPUs, 8GB RAM (half the M4's resources)
- Auto-starts on login (login item + AutoStart setting)
- `credsStore` removed from `~/.docker/config.json` — required for SSH docker pulls to work

## Caddy Reverse Proxy

- Installed via Homebrew at `/opt/homebrew/bin/caddy` (v2.11.2)
- Caddyfile: `~/services/config/Caddyfile` (version-controlled in repo at `config/Caddyfile`)
- launchd service: `~/Library/LaunchAgents/com.caddy.server.plist` (version-controlled in `config/`)
- Data/logs: `~/services/data/caddy/` (XDG_DATA_HOME)
- Reload config: `caddy reload --config ~/services/config/Caddyfile`
- Validate config: `caddy validate --config ~/services/config/Caddyfile`

## Cloudflare Tunnel

- Tunnel name: `mac-mini`, ID: `e4978b52-8394-4f5b-b715-ee96a5a9e641`
- Config: `~/services/config/cloudflared/config.yml`
- Credentials: `~/.cloudflared/<tunnel-id>.json` (not in repo)
- API token: `~/services/config/.cloudflare-token` (600 perms)
- launchd: `~/Library/LaunchAgents/com.cloudflare.cloudflared.plist`
- Zone ID: `9d3c311fe7bd41ecab3830a57a3a51a6`, Account ID: `95f53250a929e155644f51e03fc7c910`
- Cloudflare NS (for cutover): `ximena.ns.cloudflare.com`, `yew.ns.cloudflare.com`
- DNS: `test.bjblabs.com` CNAME → tunnel (ready after nameserver cutover)
- Tunnels can be created via API (`POST /accounts/{acct}/cfd_tunnel`) — no `cloudflared tunnel login` needed
- Check status: `curl -s ... /cfd_tunnel/<id>` with bearer token (see scripts)

## DNS Cutover (2026-03-17)

- Nameservers switched to Cloudflare (`ximena.ns.cloudflare.com`, `yew.ns.cloudflare.com`) — zone **active**
- All 14 Route 53 records replicated; hosted zone preserved as rollback (`Z0806990T0ZB8GBKDCD9`)
- Route 53 is the domain registrar; update via `aws route53domains update-domain-nameservers`
- Existing CloudFront services use CNAME records with `proxied: false`
- Route 53 zone deletion eligible after 2026-03-31

## Cloudflare Email Routing (LIVE as of 2026-03-18)

- Enabled and tested — podcast@ and catch-all forward to `ben.bateman.email@gmail.com`
- MX: Cloudflare (`route1/2/3.mx.cloudflare.net`); verify with `dig MX bjblabs.com +short`
- Rules API: `/zones/{zone_id}/email/routing/rules` (catch-all: `.../rules/catch_all`)
- Feature enable/destination addresses require dashboard (account-level perms)
- **Impact:** Old SES MX deleted — legal podcast email pipeline broken until Issue #9

## Cloudflare Zero Trust (NOT YET ENABLED)

- Documentation: `docs/zero-trust-setup.md` (repo), `~/services/config/zero-trust-setup.md` (Mac Mini)
- Current API token lacks Access/Zero Trust permissions — setup requires dashboard
- Not blocking Issue #7 (OpenClaw deployment)

## Service Routing Architecture

- Internet → Cloudflare (proxied CNAME) → cloudflared tunnel → Caddy (:80) → service
- cloudflared has single catch-all ingress rule → Caddy handles host-based routing
- Add new services: (1) Caddy host-matched route, (2) Cloudflare CNAME DNS record
- `openclaw.bjblabs.com` → `localhost:18789` (gateway, LIVE)

## OpenClaw on Mac Mini (DEPLOYED as of 2026-03-18)

- **Version:** v2026.3.12 (pinned — HEAD has plugin validation regression)
- **Containers:** `openclaw-gateway` (healthy), `openclaw-sandbox-browser` (healthy)
- **Ports:** 18789 (gateway), 18790 (bridge), 8788 (webhook)
- **Directory:** `~/services/openclaw/` (compose, .env, .openclaw, repo, sandbox-browser-custom)
- **Build context:** `~/services/openclaw/repo/` (cloned from github.com/openclaw/openclaw)
- Start Docker headlessly: `nohup /Applications/Docker.app/Contents/MacOS/com.docker.backend --start-docker-desktop > /dev/null 2>&1 &`
- Start OpenClaw: `cd ~/services/openclaw && docker compose up -d`
- **Known issues:** Telegram bot conflicts with EC2 instance (409 getUpdates), gog binary missing (Gmail watcher disabled)
- **Remaining:** Setup-token (Issue #35), Caddy+Tunnel wiring (#33), Gmail Pub/Sub (#34)
- Full ARM64 notes: `docs/arm64-notes.md`

## OpenClaw EC2 (still running)

- EC2 SSH: `ssh ubuntu@100.90.248.10` (via Tailscale)
- Export tarball: `~/services/data/openclaw-export.tar.gz` (on Mac Mini, 304 MB)
- Claude session keys empty — need regeneration via `openclaw setup-token` (Issue #35)
- Full docs: `docs/ec2-export-manifest.md`, `docs/environment-variables.md`
- No CI configured for this repo

## Gotchas

- `systemsetup` commands emit `Error:-99` on modern macOS — this is cosmetic, settings still apply
- The firewall `--setglobalstate on` command produces no output on success
- Remote user is `ben` (lowercase), not `Ben` — despite the Mac hostname showing "Ben"
- SSH non-interactive sessions have minimal PATH — `~/.zshenv` adds `/usr/local/bin` and `/opt/homebrew/bin`
- Docker Desktop `credsStore: desktop` uses macOS keychain, fails in SSH sessions (keychain locked)
- Docker Desktop installer: `/Applications/Docker.app/Contents/MacOS/install --accept-license --user ben`
- Docker Desktop doesn't auto-start via SSH — use `com.docker.backend --start-docker-desktop`
- cloudflared arg order matters: `cloudflared tunnel --config <path> run` (--config before run)
- OpenClaw sandbox-browser needs custom CDP proxy for Host header rewriting (Chromium rejects Docker service names)
- OpenClaw non-loopback binding requires `gateway.controlUi.dangerouslyAllowHostHeaderOriginFallback: true`
- x86_64 Playwright browsers from EC2 export are incompatible with ARM64 — delete `.playwright-browsers/`
- `launchctl load/unload/bootstrap` fails via SSH (exit 134) — launchd needs interactive login session. Use `nohup <cmd> &` over SSH; LaunchAgents will auto-start on next GUI login/reboot

## Repo Conventions

- All work tracked via GitHub Issues with `migration` label
- Issues are numbered sequentially and should be worked in order
- Direct commits to `main` (no feature branches for autonomous work)
- Commit messages reference issue numbers: `feat: ... Part of #N` or `Closes #N`
- HANDOFF.md is gitignored — transient file for human-agent handoffs when interactive steps are needed
- Documentation deployed to both `docs/` (repo) and `~/services/config/` (Mac Mini)
