# Session Log

Raw session history for the mac-mini-server project.

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

**Mistakes made:**
- Initial launchd plist had wrong arg order (`run` before `--config`) — cloudflared showed help instead of running

---

## Agent Session - Issue #5 (API rules + updated handoff)

**Worked on:** Issue #5 - Cloudflare Email Routing (routing rules via API)

**What I did:**
- Discovered the API token CAN create/edit/delete email routing rules at zone level (previous agent said it couldn't)
- Created `podcast@bjblabs.com` → `ben.bateman.email@gmail.com` forwarding rule via API
- Updated catch-all rule from disabled "drop" to enabled "forward to Gmail" via the `catch_all` endpoint
- Updated HANDOFF.md to reflect that rules are already created — human only needs to enable Email Routing in dashboard

**What I learned:**
- The API token has zone-level email routing rule permissions but NOT account-level permissions
- Zone endpoints that work: GET/POST/PUT/DELETE `/zones/{zone_id}/email/routing/rules`
- Zone endpoints that fail (auth error): GET `/zones/{zone_id}/email/routing`, POST `/zones/{zone_id}/email/routing/enable`
- Catch-all rule must be updated via `/email/routing/rules/catch_all` endpoint, NOT by ID

**Mistakes made:**
- Created redundant `config/email-routing.md` before checking that `docs/email-routing.md` already existed — cleaned up

---

## Agent Session - Issue #5 (COMPLETED, 2026-03-18)

**Worked on:** Issue #5 - Cloudflare Email Routing (human completed dashboard steps)

**What I did:**
- Guided Ben through Cloudflare Dashboard Email Routing setup
- Advised using `podcast@bjblabs.com` as initial address (real use case from legal podcast)
- Confirmed deleting old AWS SES MX record was safe (with caveat about legal podcast pipeline)
- Verified MX records now point to Cloudflare (`route1/2/3.mx.cloudflare.net`)
- Ben sent test email — confirmed delivery to Gmail
- Closed issue #5 on GitHub

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

**Mistakes made:**
- None

---

## Agent Session - Issue #7 (Sub-issue #31)

**Worked on:** Issue #7 - Migrate OpenClaw from EC2 to Mac Mini (sub-issue: openclaw-deployment#31 - Export config & data from EC2)

**What I did:**
- SSH'd to EC2 via Tailscale (`ubuntu@100.90.248.10`), confirmed connectivity
- Exported `~/.openclaw/`, `~/openclaw/.env`, `docker-compose.yml`, all Dockerfiles, `docker-setup.sh`, `~/.config/gogcli/` into tarball
- Transferred tarball EC2 → laptop → Mac Mini (`~/services/data/openclaw-export.tar.gz`, 304 MB)
- Verified file counts match
- Documented export manifest and environment variables

**What I learned:**
- EC2 OpenClaw uses Tailscale for access (IP: 100.90.248.10), not a standard SSH alias
- No Docker volumes in use — everything is bind-mounted from `~/.openclaw/` and `~/.config/gogcli/`
- Two locally-built Docker images: `openclaw:local` and `openclaw-sandbox-browser:bookworm-slim`
- Playwright browsers (~250 MB) are the bulk of the export

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
6. Both containers running and healthy on Mac Mini

**What I learned:**
- Docker Desktop on Mac Mini doesn't auto-start via SSH — use `nohup com.docker.backend --start-docker-desktop`
- OpenClaw HEAD (main) has plugin validation regression — pinned to v2026.3.12
- Non-loopback gateway binding requires `dangerouslyAllowHostHeaderOriginFallback: true`
- x86_64 Playwright browsers from EC2 incompatible with ARM64 — use image-built browsers
- Docker Desktop on macOS handles uid mapping transparently via VirtioFS

**Mistakes made:**
- First tried building from HEAD — wasted time on plugin validation errors before discovering v2026.3.12 works
- Initially forgot `OPENCLAW_BROWSER_NO_SANDBOX` env var — sandbox-browser healthcheck failed silently

---

## Agent Session - Issue #7 (Sub-issue #33)

**Worked on:** openclaw-deployment#33 - Wire OpenClaw through Caddy + Cloudflare Tunnel

**What I did:**
1. Updated Caddyfile with host-matched route: `openclaw.bjblabs.com` → `localhost:18789`
2. Created DNS CNAME in Cloudflare: `openclaw.bjblabs.com` → tunnel, proxied
3. Verified end-to-end: `https://openclaw.bjblabs.com/healthz` returns `{"ok":true}`

**What I learned:**
- cloudflared catch-all means no config changes needed for new services — just Caddy route + CNAME
- `launchctl` commands fail via SSH (exit 134) — services started via `nohup` work fine

**Mistakes made:**
- None significant.

---

## Agent Session - Issue #7 (Sub-issue #34)

**Worked on:** Issue #34 - Reconfigure Gmail Pub/Sub webhook

**What I did:**
1. Found gog binary missing in Docker — downloaded ARM64 Linux v0.12.0 from steipete/gogcli
2. Added volume mount in docker-compose.yml: `./bin/gog:/usr/local/bin/gog:ro`
3. Updated `hooks.gmail.serve.bind` from `127.0.0.1` to `0.0.0.0` in openclaw.json
4. Added Caddy route: `/gmail-pubsub*` on `openclaw.bjblabs.com` → `localhost:8788`
5. Updated Pub/Sub subscription push endpoint via gcloud on EC2
6. Verified stale notifications immediately arrived through new path

**What I learned:**
- Docker bridge: 127.0.0.1 bind inside container unreachable from host — must use 0.0.0.0
- gcloud CLI is on EC2 but not Mac Mini — used EC2 to manage GCP Pub/Sub
- GCP project: `vast-nectar-487617-j6`, subscription: `gog-gmail-watch-push`

**Mistakes made:**
- Shell escaping of `${}` in SSH commands — use `sed` instead of Python string replace

---

## Agent Session - Issue #7 (Sub-issues #35 & #36 Phase 1)

**Worked on:** Issue #7 - Sub-issues #35 (Claude auth) and #36 (EC2 decommission Phase 1)

**What I did:**
- Verified Claude auth token works for all three tiers (Opus, Sonnet, Haiku)
- Added Haiku as fallback #2
- Removed empty legacy CLAUDE_* env vars from .env
- Stopped EC2 instance i-0cc417431630fdfc5 (Phase 1 of #36)
- Documented Phase 2 (terminate after 2026-03-25) in issue comment

**What I learned:**
- OpenClaw auth uses `auth-profiles.json`, not environment variables
- `openclaw agent --agent main --message "..." --json` tests model responses via CLI
- EC2: i-0cc417431630fdfc5, EBS vol-049b363e353fd31f9, SG sg-084a0cd9295dfe466

**Mistakes made:**
- None significant.

---

## Agent Session - Issue #8 (Sub-issues #16, #17)

**Worked on:** Issue #8 - Migrate Anki Renderer + DNS cutover (sub-issues anki-renderer#16 and #17)

**What I did:**
1. Built WASM + demo in anki-renderer repo, deployed to `~/services/anki-renderer/dist/` on Mac Mini
2. Added Caddy file_server route for `anki-renderer.bjblabs.com`
3. Updated CNAME from CloudFront to tunnel via Cloudflare API
4. Verified HTTPS access, exported Route 53 records, wrote DNS cutover runbook
5. Closed both sub-issues

**What I learned:**
- cloudflared catch-all = no config changes for new services — just Caddy route + CNAME
- `scp -r dir/ remote:target/` fails if target doesn't exist; `mkdir -p` first
- anki-renderer needs both `build:wasm` (Rust→WASM) and `demo:build` (Vite) steps

**Mistakes made:**
- None.

---

## Agent Session - Issue #8 (sub-issue #18)

**Worked on:** Issue #8 - sub-issue anki-renderer#18 - Update CI/CD for Mac Mini deploy

**What I did:**
- Created deploy webhook server (`scripts/deploy-webhook.py`) with bearer token auth
- Added Caddy route for `/_deploy` path → webhook on port 9001
- Created launchd plist for webhook persistence
- Updated GitHub Actions deploy.yml: replaces CDK deploy with tarball POST
- Set `DEPLOY_WEBHOOK_SECRET` GitHub secret, verified end-to-end pipeline

**What I learned:**
- Mac Mini has no Rust/wasm-pack — builds must happen in GitHub Actions
- Python 3.9.6 (system Python) works for simple HTTP webhook
- Webhook approach ideal since no public SSH and Zero Trust not set up
- SSH command expansion: `$(cat ...)` in double-quoted ssh expands locally; use single quotes

**Mistakes made:**
- Test deploy replaced real demo files — test non-destructively or have restore plan

---

## Agent Session - Issue #8 (sub-issue anki-renderer #19)

**Worked on:** anki-renderer #19 - Delete AnkiRendererDemoStack

**What I did:**
- Surveyed all 8 open issues — most time-gated or dependency-blocked
- Verified demo works on Mac Mini and DNS is on Cloudflare
- Inventoried all 15 AWS resources in the CDK stack
- Found leftover `github-actions-anki-renderer` IAM role (not in CDK stack)
- Found stale `AWS_ROLE_ARN` GitHub secret to remove
- Confirmed OIDC provider should NOT be deleted (shared across repos)
- Wrote HANDOFF.md with cleanup instructions

**What I learned:**
- CDK stack has auto-delete bucket config, `cdk destroy` handles emptying S3
- OIDC provider is shared across repos — don't delete per-repo
- Deploy workflow already fully migrated — no AWS references remain

**Mistakes made:**
- None
