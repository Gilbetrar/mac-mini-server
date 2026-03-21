# Session Log

Raw session history for the mac-mini-server project.

---

## Agent Session - Issue #10

**Worked on:** Issue #10 - Monitoring & health checks

**What I did:**
- Created `scripts/health-check.sh` with 8 service checks: caddy process, cloudflared process, caddy HTTP, anki-renderer, openclaw-gateway, openclaw-docker, deploy-webhook, cloudflare-tunnel (external)
- Created `config/com.bjblabs.healthcheck.plist` launchd job (every 5 minutes)
- Deployed both to Mac Mini, tested — all 8 checks pass
- Verified Telegram alert delivery works
- Loaded launchd job — running on schedule

**What I learned:**
- No CI workflows exist in this repo — no need to wait for CI
- The deploy-webhook (port 9001) returns non-200 for bare requests, so the check uses `|| [[ $? -eq 22 ]]` (curl error 22 = HTTP error response, meaning the server IS responding)
- State-file approach for idempotent alerts works well: `.failing` file created on first failure, removed on recovery

**Codebase facts discovered:**
- `~/services/scripts/` directory didn't exist on Mac Mini before this session
- `~/services/data/health-check/` is used for logs and alert state files
- All 8 services were healthy at time of deployment

**Still remaining for issue #10:**
- Cloudflare external health checks (mentioned in issue but lower priority — the script already does external checks via curl to the public URL)
- Issue not closed yet — may want Cloudflare health checks added

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

## Agent Session - Issue #11

**Worked on:** Issue #11 - Backup strategy

**What I did:**
1. Created S3 bucket `bjblabs-backups-719390918663` in us-east-1
2. Created dedicated IAM user `mac-mini-backup` with policy scoped to only the backup bucket
3. Installed AWS CLI on Mac Mini via Homebrew (wasn't installed despite issue comment saying it was)
4. Configured AWS credentials on Mac Mini (`~/.aws/credentials` + `~/.aws/config`)
5. Wrote `scripts/backup.sh` — daily tarball of `config/` + `data/`, excluding logs
6. Created `config/com.bjblabs.backup.plist` — runs daily at 3am
7. Wrote `config/restore-procedure.md` — local, S3, and disaster recovery restore paths
8. Deployed all three files to Mac Mini
9. Ran backup successfully — 292MB tarball, synced to S3 (~65 seconds)
10. Verified idempotency — re-run skips if today's backup exists
11. Tested restore — extracted file from tarball, verified contents match
12. Loaded launchd job — confirmed running

**What I learned:**
- AWS CLI was NOT pre-installed on Mac Mini (issue comment was wrong) — `brew install awscli` works fine
- Backup size is ~292MB, mostly from OpenClaw data (`data/openclaw/` and `openclaw-export.tar.gz`)
- S3 sync at ~4.5 MiB/s from Mac Mini — acceptable for daily off-site backup
- No CI workflows in this repo (confirmed from previous session)

**Codebase facts discovered:**
- `~/services/backups/` directory existed but was empty
- `~/services/data/` is 317MB, `~/services/config/` is 40K
- `~/.zshenv` adds `/usr/local/bin` and `/opt/homebrew/bin` to PATH for SSH sessions

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

## Agent Session - Issue #9 (Sub-issue legal-podcast#58)

**Worked on:** Issue #9 - Migrate Legal Podcast to Mac Mini (sub-issue: legal-podcast#58 - Design local architecture)

**What I did:**
1. Explored the entire legal-podcast codebase: all 4 Lambda handlers, shared utilities, CDK stack, admin UI
2. Created three architecture design documents in the legal-podcast repo:
   - `docs/local-architecture.md` — Full architecture: Express service on port 9002, filesystem storage, Resend for email, Caddy routing, async background processing
   - `docs/lambda-to-express-mapping.md` — Lambda → Express route mapping for all handlers + shared utilities
   - `docs/storage-mapping.md` — S3 prefix → local filesystem path mapping with URL conversion
3. Incorporated decisions from issue comments: Resend for outbound email, remove Polly, .env for secrets, Cloudflare Email Workers for inbound
4. Committed to legal-podcast main, pushed, CI passed, closed issue #58

**What I learned:**
- Legal podcast has 4 Lambda handlers chained via S3 events: email-receiver → document-processor → feed-updater, plus admin-api
- Pipeline is event-driven (S3 triggers) on AWS but can be simplified to direct function calls on Mac Mini
- email-receiver gets raw MIME from S3 (SES stores it there), document-processor does text extraction → citation cleaning → TTS → audio, feed-updater regenerates RSS
- Admin UI is vanilla HTML/CSS/JS with JWT auth — no build step needed
- Workspace packages (document-processor, citation-cleaner, tts, rss, redline-generator) are all portable — no AWS dependencies
- Only two touchpoints need replacing: S3 storage (→ filesystem) and SES email (→ Resend)
- Email pipeline is BROKEN since 2026-03-17 DNS cutover — MX records moved to Cloudflare, SES can no longer receive

**Codebase facts discovered:**
- legal-podcast is a turborepo monorepo with 8 workspace packages
- Lambda handlers are in `infra/lib/handlers/` (not the `lambdas/` directory which has older standalone versions)
- Shared S3 utilities in `infra/lib/handlers/shared/s3.ts` are the single point to replace for storage
- Shared email utilities in `infra/lib/handlers/shared/email.ts` — only `sendEmail()` touches SES
- TTS providers: currently Polly + OpenAI + Kokoro; Polly being removed per issue #63

**Mistakes made:**
- None

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
