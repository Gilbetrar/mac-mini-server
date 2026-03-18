# Session Log

Raw session history for the mac-mini-server project.

---

## Agent Session - Issue #1

**Worked on:** Issue #1 - macOS server hardening

**What I did:**
- Verified SSH connectivity to Mac Mini (`ssh mac-mini`)
- Disabled computer sleep via `systemsetup -setcomputersleep Never`
- Disabled display/disk sleep via `pmset -a displaysleep 0 sleep 0 disksleep 0`
- Enabled auto-restart after power failure via `systemsetup -setrestartpowerfailure on`
- Enabled macOS firewall via `socketfilterfw --setglobalstate on`
- Created directory structure: `~/services/`, `~/services/config/`, `~/services/data/`, `~/services/backups/`
- All 5 verification checks from the issue passed

**What I learned:**
- `systemsetup` emits Error:-99 on modern macOS (Sequoia 26.x) — cosmetic, settings apply correctly
- `socketfilterfw --setglobalstate on` produces no output on success
- The remote user is `ben` (lowercase) even though the Mac shows "Ben" in its hostname

**Codebase facts discovered:**
- Repo was completely empty (no commits) — this was the first session
- 13 open issues, all labeled `migration`, numbered 1-13
- Issues designed to be worked sequentially

**Mistakes made:**
- None

---

## Agent Session - Issue #2

**Worked on:** Issue #2 - Install Docker Desktop

**What I did:**
- Downloaded Docker Desktop ARM64 .dmg from Docker's website
- Installed to /Applications via cp -R from mounted .dmg
- Ran the installer with `--accept-license --user ben` to complete first-run setup
- Created CLI symlinks in /usr/local/bin (docker, kubectl, credential helpers)
- Created `~/.zshenv` with PATH export so SSH non-interactive sessions can find docker
- Configured resource limits: 4 CPUs, 8GB RAM, 64GB disk via settings-store.json
- Configured log rotation via daemon.json (json-file, 10MB max, 3 files)
- Added Docker Desktop as macOS login item for auto-start on boot
- Removed `credsStore: desktop` from Docker config.json to fix keychain issues in SSH
- Erased stored Docker Hub credentials from keychain credential store
- Verified: docker --version, aarch64 architecture, hello-world runs, resource limits applied

**What I learned:**
- Docker Desktop for Mac uses `~/Library/Group Containers/group.com.docker/settings-store.json` for settings
- SSH non-interactive sessions don't source .zshrc — need .zshenv for PATH
- Docker Desktop's `credsStore: desktop` uses macOS keychain, which is locked in SSH sessions
- Must erase stored keychain credentials AND remove credsStore from config for SSH docker pull to work
- The Docker Desktop installer at `/Applications/Docker.app/Contents/MacOS/install` has useful subcommands: `config`, `socket-symlink-on-startup`, etc.
- `AutoStart: true` in settings-store.json plus macOS login item ensures Docker starts after reboot
- Docker Desktop settings key names are case-sensitive: `Cpus` (not `CPUs`) is what gets written to settings

**Codebase facts discovered:**
- Previous agent created scripts/01-*.sh pattern — following with scripts/02-install-docker.sh
- No package.json/build system — this is pure infrastructure/documentation repo

**Mistakes made:**
- Initially tried to run docker before the install completed — Docker Desktop needs GUI-based first run or `install --accept-license`
- Credential helper keychain issue took several attempts to diagnose — the fix was removing stored credentials AND the credsStore config

---

## Agent Session - Issue #3

**Worked on:** Issue #3 - Install Caddy reverse proxy

**What I did:**
- Installed Caddy v2.11.2 via Homebrew on Mac Mini
- Created Caddyfile at ~/services/config/Caddyfile with placeholder response on :80
- Configured Caddy log rotation (10MB per file, 5 files) via Caddyfile `log` directive
- Created launchd plist at ~/Library/LaunchAgents/com.caddy.server.plist
- Service auto-starts on login with KeepAlive enabled
- Caddy data dir set to ~/services/data/caddy/ via XDG_DATA_HOME
- Verified all acceptance criteria: version, config valid, service loaded, curl responds

**What I learned:**
- Homebrew Caddy installs to /opt/homebrew/bin/caddy (ARM64 Mac)
- Caddy has built-in log rotation via `roll_size` and `roll_keep` directives
- `caddy validate --config <path>` checks syntax; `caddy reload --config <path>` applies changes live
- `caddy fmt --overwrite` auto-formats Caddyfile
- launchd KeepAlive ensures Caddy restarts if it crashes
- Caddy's global options block (the `{ }` at top of Caddyfile) configures logging, etc.

**Codebase facts discovered:**
- Added config/ directory for version-controlled config files (Caddyfile, launchd plist)
- Script naming follows pattern: scripts/NN-description.sh

**Mistakes made:**
- None

---

## Agent Session - Issue #4 (partial)

**Worked on:** Issue #4 - Cloudflare setup + Tunnel (prep work only)

**What I did:**
- Installed cloudflared v2026.3.0 via Homebrew on Mac Mini
- Created tunnel config template at config/cloudflared/config.yml
- Created launchd plist at config/com.cloudflare.cloudflared.plist
- Created setup script scripts/04-setup-cloudflare-tunnel.sh for post-auth steps
- Created HANDOFF.md with exact instructions for interactive auth steps
- Created ~/services/config/cloudflared/ directory on Mac Mini

**Why PAUSED:**
- `cloudflared tunnel login` requires interactive browser authentication
- bjblabs.com must be added to Cloudflare dashboard manually (GUI)
- Both steps require human interaction — can't be done autonomously

**What the human needs to do:**
1. Add bjblabs.com to Cloudflare dashboard (free plan, don't change nameservers)
2. Run `ssh -t mac-mini "cloudflared tunnel login"` and authorize in browser
3. Either run `./scripts/04-setup-cloudflare-tunnel.sh` or let next agent finish

**What I learned:**
- `cloudflared tunnel login` prints a URL for browser-based OAuth, saves cert to ~/.cloudflared/cert.pem
- HANDOFF.md is gitignored by design — it's a transient communication file
- cloudflared installs cleanly via Homebrew on ARM64 Mac

**Mistakes made:**
- None

---

## Agent Session - Issue #4 (completion)

**Worked on:** Issue #4 - Cloudflare setup + Tunnel (completing after human auth)

**What I did:**
- User provided Cloudflare API token (created per handoff instructions)
- Saved token to ~/services/config/.cloudflare-token (chmod 600)
- Verified token via Cloudflare API — active and valid
- Found zone ID for bjblabs.com (9d3c311fe7bd41ecab3830a57a3a51a6)
- Created tunnel "mac-mini" via Cloudflare API (not cloudflared CLI, since no cert.pem)
- Saved tunnel credentials JSON to ~/.cloudflared/
- Deployed config.yml with real tunnel UUID
- Created DNS CNAME: test.bjblabs.com → tunnel
- Fixed launchd plist arg order (--config must come before run)
- Tunnel running with 4 healthy QUIC connections

**What I learned:**
- Can create tunnels via Cloudflare API with an API token — no need for `cloudflared tunnel login` at all
- API endpoint: POST /accounts/{acct}/cfd_tunnel with tunnel_secret (base64 random)
- The API response includes a `credentials_file` object — save it to ~/.cloudflared/<tunnel-id>.json
- cloudflared arg order: `tunnel --config <path> run` not `tunnel run --config <path>`
- DNS CNAME for tunnel: point to `<tunnel-id>.cfargotunnel.com` with proxied=true
- Cloudflare NS for bjblabs.com: ximena.ns.cloudflare.com, yew.ns.cloudflare.com

**Mistakes made:**
- Initial launchd plist had wrong arg order (`run` before `--config`) — cloudflared showed help instead of running

---

## Agent Session - Issue #5 (prep)

**Worked on:** Issue #5 - Cloudflare Email Routing (documentation + handoff)

**What I did:**
- Verified cloudflared tunnel is running (PID 7009, healthy) on Mac Mini
- Found that the Cloudflare API token exists but only has DNS/zone permissions — not email routing
- Created `docs/email-routing.md` with full documentation (routes, adding/removing, MX records, troubleshooting)
- Deployed documentation to Mac Mini at `~/services/config/email-routing.md`
- Created HANDOFF.md with step-by-step dashboard instructions for enabling Email Routing
- HANDOFF offers two paths: manual dashboard config or adding API token permissions for next agent

**Why PAUSED:**
- Cloudflare Email Routing API requires "Email Routing Addresses:Edit" and "Email Routing Rules:Edit" permissions
- The existing API token only has `#zone_settings:read/edit`, `#zone:read`, `#dns_records:read/edit`
- Need human to either configure in dashboard or update token permissions

**What I learned:**
- Cloudflare Email Routing is a separate permission scope from DNS/zone management
- bjblabs.com zone status is "pending" (nameservers not yet switched, expected)
- Zone was created 2026-03-17, account ID: 95f53250a929e155644f51e03fc7c910
- API endpoint for email routing: GET /zones/{zone_id}/email/routing

**Mistakes made:**
- None

---

## Agent Session - Issue #5 (API rules + updated handoff)

**Worked on:** Issue #5 - Cloudflare Email Routing (routing rules via API)

**What I did:**
- Discovered the API token CAN create/edit/delete email routing rules at zone level (previous agent said it couldn't)
- Created `podcast@bjblabs.com` → `ben.bateman.email@gmail.com` forwarding rule via API
- Updated catch-all rule from disabled "drop" to enabled "forward to Gmail" via the `catch_all` endpoint
- Updated HANDOFF.md to reflect that rules are already created — human only needs to enable Email Routing in dashboard
- Removed redundant `config/email-routing.md` (docs/email-routing.md is the canonical version)

**What I learned:**
- The API token has zone-level email routing rule permissions but NOT account-level permissions
- Zone endpoints that work: GET/POST/PUT/DELETE `/zones/{zone_id}/email/routing/rules`
- Zone endpoints that fail (auth error): GET `/zones/{zone_id}/email/routing`, POST `/zones/{zone_id}/email/routing/enable`
- Account endpoints that fail: GET `/accounts/{acct}/email/routing/addresses`
- Catch-all rule must be updated via `/email/routing/rules/catch_all` endpoint, NOT by ID
- Forwarding rules can be created even without a verified destination address (may need verification before delivery works)

**Mistakes made:**
- Created redundant `config/email-routing.md` before checking that `docs/email-routing.md` already existed — cleaned up

---

## Agent Session - Issue #5 (Completion Handoff)

**Worked on:** Issue #5 - Cloudflare Email Routing (final steps)

**What I learned:**
- The `/zones/{zone_id}/email/routing` status endpoint and `/zones/{zone_id}/email/routing/enable` endpoint both require account-level permissions not present in the current API token
- The `/zones/{zone_id}/email/routing/rules` endpoint works fine with the current token — rules can be read/created/modified
- Both routing rules (podcast@ and catch-all) are confirmed present and enabled via API
- Enabling Email Routing is genuinely dashboard-only with the current token scope

**Codebase facts discovered:**
- HANDOFF.md is gitignored (per LEARNINGS.md) so it won't be committed

**What I did:**
- Verified routing rules exist and are enabled via API
- Attempted to enable email routing via API (confirmed auth error)
- Created HANDOFF.md with detailed steps for the human to complete in Cloudflare Dashboard
- Signaled PAUSED for human action

**Mistakes made:**
- None

---

## Agent Session - Issue #5 (Iteration 6)

**Worked on:** Issue #5 - Cloudflare Email Routing (handoff verification)

**What I did:**
- Verified routing rules still exist and are enabled via API (podcast@ and catch-all both active)
- Confirmed MX records still point to AWS SES (`inbound-smtp.us-east-1.amazonaws.com`) — Email Routing not yet enabled
- Confirmed API token cannot access `/email/routing`, `/email/routing/enable`, or `/email/routing/dns` endpoints (auth error)
- Updated HANDOFF.md with current verification state
- Signaled PAUSED for human dashboard action

**What I learned:**
- The Cloudflare API token has granular permissions — `/email/routing/rules` works but settings/enable/dns endpoints don't
- MX record check (`dig MX bjblabs.com +short`) is a reliable way to verify if Email Routing is enabled
- HANDOFF.md already existed from a previous session — this is the second time this handoff has been surfaced

**Codebase facts discovered:**
- HANDOFF.md is gitignored (per LEARNINGS.md)
- Previous agents already did all API-accessible work for issue #5

**Mistakes made:**
- None — this was a straightforward verification and handoff update

---

## Agent Session - Issue #5 (Handoff Re-check)

**Worked on:** Issue #5 - Cloudflare Email Routing (third handoff attempt)

**What I learned:**
- Email Routing still not enabled — MX records still point to AWS SES (`inbound-smtp.us-east-1.amazonaws.com`)
- The two API-created routing rules (podcast@ and catch-all) are still present and enabled
- The `/zones/{zone_id}/email/routing` and `/zones/{zone_id}/email/routing/enable` endpoints both return auth errors with the current token
- This is the third agent session surfacing the same handoff — the human hasn't completed the dashboard steps yet
- Re-created HANDOFF.md with clear step-by-step instructions

**Codebase facts discovered:**
- HANDOFF.md was absent (cleaned up or never committed), so a new one was needed
- All prior API work from issue #5 is still intact

**Mistakes made:**
- None

---

## Agent Session - Issue #5 (COMPLETED, 2026-03-18)

**Worked on:** Issue #5 - Cloudflare Email Routing (human completed dashboard steps)

**What I did:**
- Guided Ben through Cloudflare Dashboard Email Routing setup
- Advised using `podcast@bjblabs.com` as initial address (real use case from legal podcast)
- Confirmed deleting old AWS SES MX record was safe (with caveat about legal podcast pipeline)
- Verified MX records now point to Cloudflare (`route1/2/3.mx.cloudflare.net`)
- Verified both routing rules (podcast@ and catch-all) still active via API
- Ben sent test email — confirmed delivery to Gmail
- Closed issue #5 on GitHub
- Updated LEARNINGS.md with completion status and SES impact note
- Cleaned up HANDOFF.md

**What I learned:**
- Legal podcast project depends on SES email receiving: email → SES → S3 → Lambda (extracts DOCX → generates podcast)
- Deleting SES MX record breaks that pipeline — must be addressed in Issue #9
- Cloudflare Email Routing setup wizard requires at least one custom address to get started

**Mistakes made:**
- None

---

## Agent Session - Issue #6

**Worked on:** Issue #6 - Cloudflare Zero Trust

**What I did:**
- Created comprehensive Zero Trust setup documentation at `docs/zero-trust-setup.md`
- Copied documentation to Mac Mini at `~/services/config/zero-trust-setup.md`
- Wrote HANDOFF.md with 3 dashboard steps for Ben (enable free plan, verify OTP, optionally update API token)
- Signaled PAUSED — dashboard steps require human action

**What I learned:**
- Current Cloudflare API token does NOT have Access/Zero Trust permissions (returns 403)
- Zero Trust enrollment and identity provider setup can only be done via dashboard (not API)
- Issue scope was simplified: OTP instead of Google OAuth, not urgent until first browser-facing service
- Issue #6 is NOT a dependency for #7 (OpenClaw) per scope clarification comment

**Codebase facts discovered:**
- HANDOFF.md is gitignored (mentioned in LEARNINGS.md)
- Project follows pattern of writing docs to both repo (`docs/`) and Mac Mini (`~/services/config/`)

**Mistakes made:**
- None

---

## Agent Session - Issue #7 (Sub-issue #31)

**Worked on:** Issue #7 - Migrate OpenClaw from EC2 to Mac Mini (sub-issue: openclaw-deployment#31 - Export config & data from EC2)

**What I did:**
- SSH'd to EC2 via Tailscale (`ubuntu@100.90.248.10`), confirmed connectivity
- Exported `~/.openclaw/`, `~/openclaw/.env`, `docker-compose.yml`, all Dockerfiles, `docker-setup.sh`, `~/.config/gogcli/` into tarball
- Transferred tarball EC2 → laptop → Mac Mini (`~/services/data/openclaw-export.tar.gz`, 304 MB)
- Verified file counts: 2,404 files on EC2 vs 2,407 in tarball (match within timing variance)
- Documented export manifest (`docs/ec2-export-manifest.md`) and environment variables (`docs/environment-variables.md`)
- Issue #31 was already closed (by prior agent or human)

**What I learned:**
- EC2 OpenClaw uses Tailscale for access (IP: 100.90.248.10), not a standard SSH alias
- No Docker volumes in use — everything is bind-mounted from `~/.openclaw/` and `~/.config/gogcli/`
- Two locally-built Docker images (not from registry): `openclaw:local` and `openclaw-sandbox-browser:bookworm-slim`
- The `gog` binary (v0.11.0) is installed at `/usr/local/bin/gog` on EC2 and bind-mounted into containers
- Playwright browsers (~250 MB) are the bulk of the export
- Claude session keys were empty at export time — will need regeneration (Issue #35)
- Issue #6 (Zero Trust) was deferred — skipped to #7 as it's unblocked
- No CI configured for mac-mini-server repo

**Codebase facts discovered:**
- OpenClaw compose has 3 services: gateway, cli, sandbox-browser
- Gateway depends on sandbox-browser health check (CDP on port 9222)
- Gmail Pub/Sub webhook runs on port 8788 inside the gateway container
- gogcli keyring password is hardcoded in docker-compose.yml (`openclaw-gog`)

**Mistakes made:**
- None

---

## Agent Session - Issue #7 / Sub-issue #32

**Worked on:** Issue #32 (openclaw-deployment) - Deploy OpenClaw on Mac Mini

**What I did:**
1. Extracted EC2 export tarball to `~/services/openclaw/` on Mac Mini
2. Cloned OpenClaw repo (v2026.3.12) for ARM64 build context
3. Built `openclaw:local` image with `OPENCLAW_INSTALL_BROWSER=1` (~4.5 GB, native ARM64)
4. Built custom `openclaw-sandbox-browser:bookworm-slim` with CDP Host-header proxy (~1.5 GB)
5. Created adapted `docker-compose.yml` and `.env` with Mac Mini paths
6. Fixed config issues: controlUi origin fallback, disabled problematic extensions
7. Both containers running and healthy on Mac Mini

**What I learned:**
- Docker Desktop on Mac Mini doesn't auto-start via SSH — `open -a Docker` fails. Use: `nohup /Applications/Docker.app/Contents/MacOS/com.docker.backend --start-docker-desktop > /dev/null 2>&1 &`
- OpenClaw HEAD (main) has plugin validation regression — "extension entry escapes package directory" for all built-in extensions. Pinned to v2026.3.12 which works correctly
- Non-loopback gateway binding requires `gateway.controlUi.dangerouslyAllowHostHeaderOriginFallback: true` (new in recent versions)
- Upstream sandbox-browser uses `socat` for CDP forwarding which doesn't rewrite Host headers — Chromium rejects Docker service names as Host. Custom CDP proxy (`cdp-host-proxy.py`) still needed
- Sandbox-browser needs `OPENCLAW_BROWSER_NO_SANDBOX: "1"` env var for Chromium to run in Docker
- x86_64 Playwright browsers from EC2 export are incompatible with ARM64 — deleted `.playwright-browsers/` and relied on image-built browsers instead
- EC2 commit `4e916bb25` doesn't exist in upstream repo (was a local patch). Used v2026.3.12 tag instead
- Docker Desktop on macOS handles uid mapping transparently via VirtioFS — no manual ownership changes needed

**Codebase facts discovered:**
- OpenClaw repo at `github.com/openclaw/openclaw` (public)
- Dockerfile supports ARM64 natively with multi-stage build
- `OPENCLAW_INSTALL_BROWSER=1` build arg installs Playwright Chromium during image build
- gog binary can't be host-mounted (macOS binary ≠ Linux container) — need Linux ARM64 build or container install

**Mistakes made:**
- First tried building from HEAD — wasted time on plugin validation errors before discovering v2026.3.12 works
- Initially forgot `OPENCLAW_BROWSER_NO_SANDBOX` env var — sandbox-browser healthcheck failed silently (just connection refused)

**Status:** Containers healthy. Telegram bot has 409 conflict with EC2 (expected — both running same bot token). Gmail watcher disabled (gog binary missing). Next steps: issue #33 (Caddy + Tunnel wiring), #34 (Gmail webhook), #35 (setup-token).

---

## Agent Session - Issue #7 (Sub-issue #33)

**Worked on:** openclaw-deployment#33 - Wire OpenClaw through Caddy + Cloudflare Tunnel

**What I did:**
1. Updated Caddyfile with host-matched route: `openclaw.bjblabs.com` → `localhost:18789` (gateway)
2. Created DNS CNAME in Cloudflare: `openclaw.bjblabs.com` → tunnel (`e4978b52-...cfargotunnel.com`), proxied
3. Deployed Caddyfile to Mac Mini, restarted Caddy and cloudflared
4. Verified end-to-end: `https://openclaw.bjblabs.com/healthz` returns `{"ok":true,"status":"live"}`

**What I learned:**
- cloudflared config doesn't need per-service ingress rules — the catch-all route sends everything to Caddy, which handles host-based routing
- Caddy `@matcher host` syntax works well for multi-service routing on a single `:80` listener
- The cloudflared config already had the right architecture (single catch-all to Caddy)

**Codebase facts discovered:**
- `launchctl load/unload/bootstrap/print` all fail via SSH with exit 134 or "Domain does not support specified action" — launchd needs an interactive login session on modern macOS
- Services started via `nohup` work fine but won't auto-restart; LaunchAgent plists exist and will work on next interactive login/reboot
- The OpenClaw gateway serves its control UI + `/healthz` on port 18789; webhook port 8788 is separate

**Mistakes made:**
- None significant. Initial `caddy reload` failed because Caddy wasn't running (had stopped since previous session). Needed to start it fresh.

**Status:** Issue #33 closed. `openclaw.bjblabs.com` fully wired. Next: #34 (Gmail Pub/Sub webhook), #35 (setup-token), #36 (decommission EC2).

---

## Agent Session - Issue #7 (Sub-issue #34)

**Worked on:** Issue #34 - Reconfigure Gmail Pub/Sub webhook

**What I did:**
1. Discovered `gog` binary (gogcli) was missing in Docker container — source of "Gmail watcher disabled" error
2. Found gog is a Go binary from github.com/steipete/gogcli — downloaded ARM64 Linux v0.12.0
3. Stored binary at `~/services/openclaw/bin/gog` on Mac Mini
4. Added volume mount in docker-compose.yml: `./bin/gog:/usr/local/bin/gog:ro`
5. Updated `hooks.gmail.serve.bind` from `127.0.0.1` to `0.0.0.0` in openclaw.json (needed for Docker bridge networking)
6. Added Caddy route: `/gmail-pubsub*` on `openclaw.bjblabs.com` → `localhost:8788`
7. Updated Pub/Sub subscription push endpoint via gcloud on EC2 (gcloud not available locally/Mac Mini)
8. Old endpoint: `https://ip-172-31-31-65.tailde5b32.ts.net/gmail-pubsub?token=...`
9. New endpoint: `https://openclaw.bjblabs.com/gmail-pubsub?token=...`
10. Verified: stale Pub/Sub notifications immediately started arriving through the new path

**What I learned:**
- gog binary is from steipete/gogcli (GitHub), statically linked Go binary with linux_arm64 releases
- Docker bridge networking: 127.0.0.1 bind inside container is unreachable from host port mapping — must use 0.0.0.0
- gog serve `--path /` makes it handle all paths (default is `/gmail-pubsub`)
- OpenClaw's ensureDependency only auto-installs via Homebrew on macOS — Docker containers need manual binary installation
- gcloud CLI is on EC2 but not Mac Mini — can use EC2 to manage GCP Pub/Sub subscriptions
- The Pub/Sub subscription was using Tailscale hostname as push endpoint

**Codebase facts discovered:**
- OpenClaw Gmail watcher: gateway auto-starts `gog gmail watch serve` + `gog gmail watch start` (via startGmailWatch)
- gog watch serve is the HTTP server receiving Pub/Sub push notifications
- gog watch start tells Gmail API to push to the Pub/Sub topic
- The watcher auto-renews every 60 minutes (configurable via renewEveryMinutes)
- GCP project: `vast-nectar-487617-j6`, subscription: `gog-gmail-watch-push`
- OAuth credentials (installed/desktop type) at `.openclaw/gcloud/credentials.json`

**Mistakes made:**
- First attempt to edit docker-compose via Python string replace failed due to shell escaping of `${}` — used `sed` instead

---

## Agent Session - Issue #7 (Sub-issues #35 & #36 Phase 1)

**Worked on:** Issue #7 - Migrate OpenClaw from EC2 to Mac Mini (sub-issues #35 and #36)

**What I did:**
- Verified Claude auth token in auth-profiles.json (from EC2 export) works for all three tiers
- Tested Opus, Sonnet, and Haiku via `openclaw agent` CLI — all responded successfully
- Added Haiku as fallback #2 (was only Opus default + Sonnet fallback)
- Removed empty legacy env vars (CLAUDE_AI_SESSION_KEY, CLAUDE_WEB_SESSION_KEY, CLAUDE_WEB_COOKIE) from .env
- Created docs/claude-setup-token.md with regeneration instructions
- Deployed docs to Mac Mini at ~/services/config/claude-setup-token.md
- Sub-issue #35 was already closed (by previous agent)
- Stopped EC2 instance i-0cc417431630fdfc5 (Phase 1 of #36)
- Commented Phase 1 completion on issue #36 with all resource IDs for Phase 2 cleanup
- Wrote HANDOFF.md for Phase 2 (terminate after 2026-03-25)

**What I learned:**
- OpenClaw auth uses auth-profiles.json, not environment variables. The CLAUDE_* env vars were legacy/empty.
- `openclaw models auth add` / `paste-token` / `setup-token` are the three ways to configure auth
- `openclaw agent --agent main --message "..." --json` is the way to test model responses via CLI
- `openclaw models set` changes default; `openclaw models fallbacks add` adds fallbacks
- The EC2 instance ID is i-0cc417431630fdfc5, EBS vol-049b363e353fd31f9, SG sg-084a0cd9295dfe466

**Codebase facts discovered:**
- HANDOFF.md is gitignored (per repo conventions)
- Sub-issue #35 was already closed before this session started
- The sandbox-browser dbus/Vulkan errors in logs are cosmetic (expected in headless Docker)

**Mistakes made:**
- None significant. Initially tried `--model` flag on `openclaw agent` which doesn't exist; used `openclaw models set` instead.

---

## Agent Session - Issue #8 (Sub-issues #16, #17)

**Worked on:** Issue #8 - Migrate Anki Renderer + DNS cutover to Cloudflare (sub-issues anki-renderer#16 and #17)

**What I did:**
1. **anki-renderer#16 (Serve demo from Mac Mini):**
   - Built WASM (`npm run build:wasm`) and demo (`npm run demo:build`) in anki-renderer repo
   - Created `~/services/anki-renderer/dist/` on Mac Mini
   - Copied built demo files via `scp`
   - Added Caddy route: `@anki_renderer host anki-renderer.bjblabs.com` → `file_server` from dist/
   - Validated and reloaded Caddyfile
   - Verified via `curl -s http://localhost:80 -H 'Host: anki-renderer.bjblabs.com'` — HTML returned
   - Closed anki-renderer#16

2. **anki-renderer#17 (DNS cutover):**
   - Nameserver cutover was already done (2026-03-17) — just needed CNAME update + docs
   - Updated CNAME for `anki-renderer.bjblabs.com` from CloudFront to tunnel via Cloudflare API
   - Verified `curl -s https://anki-renderer.bjblabs.com` returns HTTP 200
   - Exported Route 53 records to `docs/route53-export.json` (16 records)
   - Wrote `docs/dns-cutover-runbook.md` with full history and rollback procedure
   - Closed anki-renderer#17

**What I learned:**
- cloudflared catch-all ingress means no cloudflared config changes needed for new services — just Caddy route + CNAME
- `scp -r dir/ remote:target/` fails if target doesn't exist; must `mkdir -p` first, then `scp -r dir/* remote:target/`
- Cloudflare DNS PATCH API to update CNAME: set `content` to tunnel CNAME and `proxied: true`

**Codebase facts discovered:**
- anki-renderer demo needs both `build:wasm` (Rust→WASM) and `demo:build` (Vite) steps
- Demo dist includes: index.html, assets/ (JS/CSS), lib/, pkg/ (WASM)
- Issue #6 (Zero Trust) is deferred per owner — not urgent until browser-facing service deployed
- Issue #7 sub-issue #36 (EC2 decommission) time-blocked until 2026-03-25

**Mistakes made:**
- None.
