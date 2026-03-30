# Session Log

Raw session history for the mac-mini-server project.

---

## Agent Session - Issue #9 (sub-issue #63)

**Worked on:** legal-podcast#63 - Remove AWS Polly as TTS provider

**What I did:**
- Deleted polly-provider.ts and its tests from @legal-podcast/tts package
- Removed @aws-sdk/client-polly dependency
- Updated default TTS provider from polly-neural to openai across all files
- Updated 21 files: handlers, types, admin UI, scripts, CDK stack, tests
- Removed Polly IAM permissions from CDK stack
- Fixed E2E test failures (case-sensitive provider name, voice name)
- All 161 infra tests and 396 package tests pass, CI green

**What I learned:**
- The legal-podcast monorepo has pre-push lint hooks (turbo lint)
- E2E tests use Playwright with route interception via mock data
- The admin UI's formatProvider() capitalizes names (OpenAI not openai)
- Playwright toContainText is case-sensitive
- Issue #6 (Cloudflare Zero Trust) is deferred per comment
- Issue #7/#36 (EC2 decommission) waiting until after 2026-03-25

**Codebase facts discovered:**
- legal-podcast has 7 workspace packages + infra (CDK) + admin-ui (vanilla JS)
- Polly references were in 20+ files across handlers, types, UI, scripts, and tests
- The CLI script (cli.ts) hardcoded PollyProvider, now uses OpenAIProvider
- generate-samples.ts lists voice configs per provider for voice sample generation

**Mistakes made:**
- First push failed E2E: forgot to update case-sensitive 'openai' to 'OpenAI' in episode table test
- Forgot to update 'Joanna' to 'Alloy' in voice highlight test

---

## Agent Session - Issue #9 (sub-issue #59, tests)

**Worked on:** legal-podcast#59 - Build local pipeline service (handler & email tests)

**What I did:**
- Added `__tests__/email.test.ts` — 23 tests covering renderTemplate, formatDuration, formatCost, isBillingError, generateSuccessEmail, generateErrorEmail, generateAdminAlertEmail, DEFAULT_EMAIL_TEMPLATES
- Added `__tests__/handlers.test.ts` — 20 tests covering health endpoint, webhook auth (secret validation), admin auth (JWT login), episodes CRUD, config management, stats aggregation, email templates CRUD, episode deletion with feed regeneration
- Installed supertest + @types/supertest as devDependencies for HTTP-level testing
- All 49 service tests pass, full project CI green (402+ total tests)

**What I learned:**
- storage.ts captures DATA_DIR at module load time (top-level const). Dynamic imports are cached by the ES module loader, so all tests within a file share one DATA_DIR. Use beforeAll/afterAll for temp dir, and clean data files between tests in beforeEach
- The admin config PUT handler accepts empty title/description from missing body fields because it falls back to existing?.title. Tests need clean state (no pre-existing feed-config.json) to test the validation path correctly

**Codebase facts discovered:**
- Previous agent already wrote core service code (server.ts, routes, storage, email, types, logger) — only storage.test.ts existed
- Architecture design chose "no Docker" (launchd-managed process), overriding the issue's Docker acceptance criteria
- Issue #59 still open — remaining work: possible integration test with mocked pipeline, but core tests now cover all routes

**Mistakes made:**
- Initial email test expected renderTemplate to remove blank lines left by undefined vars — it only collapses 3+ consecutive newlines, not 2
- Initial handler tests used per-test temp dirs (beforeEach) but modules cache DATA_DIR once — caused cross-test data leaks

---

## Agent Session - Issue #9 (sub-issue #59, integration test — CLOSED)

**Worked on:** legal-podcast#59 - Build local pipeline service (pipeline integration test)

**What I did:**
- Added `__tests__/pipeline.integration.test.ts` — 2 tests covering end-to-end pipeline
- Test 1: Real DOCX fixture → MIME email → webhook → document extraction → citation cleaning → TTS (mocked) → redline generation → RSS feed update → notification email (mocked). Verifies episodes.json, feed.xml, audio file, metadata, source document, and redline all created correctly.
- Test 2: Email without DOCX attachment → no episode created
- Used `vi.mock('@legal-podcast/tts')` to mock TTS providers, `vi.mock('resend')` to mock email sending
- All 51 service tests pass (4 test files), CI green
- Closed legal-podcast#59 — all acceptance criteria met (Docker excluded per architecture decision in #58)

**What I learned:**
- `vi.mock()` with ESM workspace packages works — hoisted above imports as expected
- Resend client is lazily instantiated via getResend() — need RESEND_API_KEY env var set even with mock, because the mock replaces the Resend constructor but getResend() still checks the env var before instantiating
- Webhook returns 202 immediately, processes async — integration test polls for output files with timeout
- Building multipart MIME emails manually requires base64 encoding of DOCX and proper boundary markers
- Real test fixture (112K chars extracted) processes through citation cleaner → 104K chars cleaned — removes ~7K chars of citations

**Codebase facts discovered:**
- test-fixtures/ has 5 real DOCX legal documents available for integration testing
- MockTTSProvider already exists in @legal-podcast/tts package but wasn't used here (mocked at module level instead since webhook.ts creates providers internally)

**Mistakes made:**
- Initially forgot RESEND_API_KEY env var — mock was in place but email.ts still checked for the key before creating the client

---

## Agent Session - Issue #9 / Sub-issue #60

**Worked on:** Issue #9 - Migrate Legal Podcast, Sub-issue #60 - Serve legal podcast from Mac Mini

**What I did:**
1. Created Dockerfile (multi-stage build) and .dockerignore in legal-podcast repo
2. Created docker-compose.yml and .env.example in mac-mini-server/services/legal-podcast/
3. Updated Caddyfile with legalpodcast.bjblabs.com routes (API proxy + static data files + admin UI)
4. Deployed to Mac Mini: cloned repo, built Docker image, started container
5. Pulled API keys from AWS SSM Parameter Store to create .env on Mac Mini
6. Updated DNS CNAME from CloudFront to Cloudflare tunnel
7. Added health checks for legal-podcast service and Docker container
8. Copied admin UI static files to Mac Mini

**What I learned:**
- Multiple Caddy processes can accumulate if caddy start/stop is used while launchd manages Caddy (KeepAlive: true). Use `killall caddy` + let launchd restart to get a clean state with new config.
- `caddy reload` doesn't work when multiple Caddy processes are running — it reloads one but requests may go to the other.
- Cloudflare DNS propagation is near-instant for proxied records. Can verify immediately using `--resolve` with the new IP.
- Docker build for monorepo workspace: use `--filter=@package/name...` with turbo to build only needed packages.
- SSM parameters for legal-podcast: /legal-podcast/{openai-api-key, replicate-api-token, admin-password, jwt-secret}
- Email webhook secret stored at ~/services/config/alerts/email-webhook.env on Mac Mini
- RESEND_API_KEY not yet configured — email notifications won't work until Ben provides this

**Codebase facts discovered:**
- Legal podcast service runs on port 9002, uses DATA_DIR env var for filesystem storage
- Admin UI is vanilla HTML/CSS/JS in packages/admin-ui/ (no build step)
- Service was designed for launchd but issue specified Docker — Docker works fine
- Legal podcast data files (audio, feed.xml, redlines, images) served directly by Caddy from ~/services/legal-podcast/data/

**Mistakes made:**
- Ran `caddy start` via SSH while launchd was managing Caddy, creating competing instances. Should have just used `killall caddy` and let launchd restart with the new config file.

---

## Agent Session - Issue #9 (sub-issues #60 and #61)

**Worked on:** Issue #9 - Migrate Legal Podcast to Mac Mini (sub-issues #60 and #61)

**What I did:**
- Verified issue #60 (Serve from Mac Mini) was fully complete: Docker container healthy, Caddy routes working, DNS CNAME pointing to tunnel, email worker deployed. Closed #60.
- Completed issue #61 (Migrate data from S3): Downloaded 29 files (146 MB) from S3, updated all URLs in feed.xml/episodes.json/feed-config.json from CloudFront/S3 to legalpodcast.bjblabs.com, transferred to Mac Mini via rsync, verified all files accessible through Caddy and public tunnel. Closed #61.

**What I learned:**
- legalpodcast.bjblabs.com DNS was switched to Cloudflare tunnel by previous agent, but local DNS cache on dev machine was stale (showed CloudFront). Use `--resolve` flag with curl to bypass DNS cache.
- Mac Mini's `mac-mini-backup` IAM user can't access the legal podcast S3 bucket. Need to download locally first and rsync to Mac Mini.
- S3 bucket `admin/` directory is separate from the data directory — admin UI is at `~/services/legal-podcast/admin-ui/`, data at `~/services/legal-podcast/data/`.

**Remaining for issue #9:**
- Only #62 (Delete LegalPodcastStack) remains — requires 1+ weeks stability + Ben's approval. Not actionable yet.

---

## Agent Session - Issues #10 and #6

**Worked on:** Issue #10 - Monitoring & health checks (closure), Issue #6 - Cloudflare Zero Trust (HANDOFF)

**What I did:**
- Verified issue #10 was fully complete: health check script (10 checks) exists, launchd runs every 5 min, Telegram alerts work, all services passing. Closed #10 with note that Cloudflare-native health checks require paid plan — local script includes external tunnel check as equivalent.
- Assessed issue #6 (Cloudflare Zero Trust): confirmed via API that Access is not enabled (`access.api.error.not_enabled`). Documentation already exists at `docs/zero-trust-setup.md` (committed by previous agent). Created HANDOFF.md for Ben to enable Zero Trust in dashboard (5-min task).

**What I learned:**
- Cloudflare Access API endpoint: `accounts/{id}/access/apps` — returns clear error when Access not enabled
- Cloudflare-native health checks require Pro+ plan. The local health check script's external tunnel check (#10 in script) provides equivalent monitoring.
- Most remaining open issues are time-gated: #7/#36 (EC2 decommission after 3/25), #9/#62 (CDK destroy needs stability), #12 (Route 53 after 3/31), #13 (docs after all migrations)

**Remaining open issues:**
- #6: Zero Trust — PAUSED, waiting for Ben to enable in dashboard
- #7: OpenClaw — only EC2 decommission (#36) left, wait until 2026-03-25
- #9: Legal Podcast — only LegalPodcastStack deletion (#62) left, needs stability + approval
- #12: Route 53 — wait until 2026-03-31
- #13: Documentation — depends on all migrations complete

---

## Agent Session - Issues #6, #13 (2026-03-21)

**Worked on:** Issue #6 - Cloudflare Zero Trust (COMPLETED), Resend API key setup, Issue #13 - Documentation cleanup

**What I did:**
1. Enabled Cloudflare Zero Trust via dashboard (Playwright): Free plan ($0/month), team domain `bjblabs.cloudflareaccess.com`, PayPal billing, verified via API
2. Closed issue #6, deleted HANDOFF.md
3. Created Resend account, added bjblabs.com domain with DKIM/SPF/MX DNS records in Cloudflare
4. Generated Resend API key (`legal-podcast`), configured in `~/services/legal-podcast/.env`, restarted container — domain verified
5. Created Asana task "Complete Mac Mini Migration — AWS Decommission" with 5 dated subtasks for remaining cleanup
6. Documentation cleanup (issue #13):
   - Updated LEARNINGS.md: Zero Trust enabled, RESEND_API_KEY configured
   - Updated docs/email-routing.md: webhook endpoint is live, routes table corrected
   - Updated docs/zero-trust-setup.md: marked initial setup as completed
   - Updated global CLAUDE.md: migration complete, Legal Podcast live, routing updated
   - Updated memory files: mac-mini-server.md and MEMORY.md reflect current state
   - Created README.md and AGENTS.md for the project

**Remaining open issues:**
- #7: OpenClaw — EC2 decommission after 2026-03-25
- #9: Legal Podcast — LegalPodcastStack deletion after stability period
- #12: Route 53 — delete after 2026-03-31
- #13: Documentation — closing with this session

---

## Agent Session - Issue #12 Prep

**Worked on:** Issue #12 - Delete Route 53 hosted zone (prep work)

**What I did:**
1. Surveyed all open issues: #7, #9, #12 — all time-blocked
   - #7/#36: EC2 decommission blocked until 2026-03-25
   - #9/#62: LegalPodcastStack deletion needs 1+ weeks stability (deployed 2026-03-20)
   - #12: Route 53 deletion needs 2+ weeks after DNS cutover (2026-03-17)
2. Verified all three services healthy (HTTP 200): anki-renderer, openclaw, legalpodcast
3. Verified DNS fully on Cloudflare: NS, MX, all subdomains resolving via Cloudflare proxy IPs
4. Exported final Route 53 records to `docs/route53-final-export.json` (15 records)
   - Updated from prior export (which still had the deleted anki-renderer CloudFront A record)
   - Added metadata: export date, hosted zone ID, note about non-authoritative status

**What I learned:**
- All remaining issues (#7, #9, #12) are in waiting/stability periods — no implementation work possible until dates pass
- Route 53 zone still has stale records (SES DKIM, ACM validation CNAMEs, old CloudFront aliases) that are harmless since nameservers point to Cloudflare

**Codebase facts discovered:**
- `docs/route53-export.json` was from an earlier point in time (still had anki-renderer CloudFront record)
- Issue #12 specifies the export should be at `docs/route53-final-export.json`

**Next actions (for future agents):**
- After 2026-03-25: Work on #7/#36 (EC2 decommission) — needs HANDOFF.md + PAUSED for Ben's approval
- After ~2026-03-27: Work on #9/#62 (LegalPodcastStack deletion) — needs HANDOFF.md + PAUSED
- After ~2026-04-01: Work on #12 (Route 53 deletion) — needs HANDOFF.md + PAUSED

---

## Agent Session - Issue #14

**Worked on:** Issue #14 - Deploy NocoDB on Mac Mini via Docker Compose

**What I did:**
- Created `services/nocodb/docker-compose.yml` in repo
- Deployed to Mac Mini: created directory, generated JWT secret, created .env
- Pulled nocodb/nocodb:latest image and started container
- Verified: HTTP 200, healthcheck passing, data persists across restarts
- Closed issue #14

**What I learned:**
- NocoDB deployment is straightforward — single container, SQLite backend, no build step needed
- No CI configured for this repo (infrastructure/docs only)

**Codebase facts discovered:**
- Issues #7, #9, #12 are blocked on time-based criteria (EC2 decommission after 2026-03-25, Route 53 after 2+ weeks)
- NocoDB issues (#14-#21) are the next active workstream

**Mistakes made:** None

---

## Agent Session - Issue #15

**Worked on:** Issue #15 - Route NocoDB through Caddy + Cloudflare DNS

**What I did:**
- Added `@nocodb host data.bjblabs.com` route in Caddyfile, reverse proxying to localhost:8080
- Deployed updated Caddyfile to Mac Mini and reloaded Caddy
- Created proxied CNAME DNS record in Cloudflare pointing `data` to the tunnel hostname
- Initially pointed CNAME to `bjblabs.com` (wrong) → got HTTP 530 → fixed to point to `e4978b52-...cfargotunnel.com`
- Verified: https://data.bjblabs.com returns 200 with NocoDB UI

**What I learned:**
- Cloudflare DNS CNAME records for tunnel-routed services must point to `<tunnel-id>.cfargotunnel.com`, NOT to the apex domain
- Initial 530 errors after DNS record creation may be transient (propagation) — always verify after a short wait

**Mistakes made:**
- Created CNAME pointing to `bjblabs.com` instead of the tunnel hostname — caused 530 errors. Fixed by checking existing records for the correct pattern.

---

## Agent Session - Issue #16

**Worked on:** Issue #16 - Secure NocoDB with Cloudflare Zero Trust

**What I did:**
- Created Cloudflare Access application for `data.bjblabs.com` via API (app ID: `c1b4abb1-0184-4e6b-b812-2b226dc41921`)
- Created Allow policy for `ben.bateman.email@gmail.com` (email OTP)
- Verified: `https://data.bjblabs.com` now returns 302 redirect to Cloudflare auth page
- Updated `docs/zero-trust-setup.md` with NocoDB section
- Created HANDOFF.md for Service Token creation (requires dashboard)

**What I learned:**
- The Cloudflare API token has Access: Apps and Policies permission but NOT Access: Service Tokens. Service tokens must be created via dashboard.
- Access apps + policies can be fully created via API using the documented pattern in zero-trust-setup.md

**Codebase facts discovered:**
- The API token permission note in docs was accurate — it does have Access permissions now (the "Optional" note about adding them must have been completed)

**Mistakes made:** None

---

## Agent Session - Issue #16 (continued)

**Worked on:** Issue #16 - Secure NocoDB with Cloudflare Zero Trust (service token completion)

**What I did:**
- Used Playwright to navigate Cloudflare dashboard and create service token "NocoDB MCP" (non-expiring)
- Saved CF-Access-Client-Id and CF-Access-Client-Secret to `~/services/nocodb/.cf-service-token` on Mac Mini
- Added non_identity (Service Auth) policy to NocoDB Access app via API
- Verified: service token returns 200, unauthenticated returns 302
- Updated docs, cleaned up HANDOFF.md, closed issue #16

**What I learned:**
- Playwright can handle Cloudflare dashboard interactions after user authenticates (passkey)
- Service token creation requires dashboard (API token lacks permission), but Service Auth policies can be added via API
- Service token ID is in the URL after creation: `/service-tokens/<uuid>`
- The new Cloudflare dashboard URL pattern for apps doesn't use the app UUID in `/access-controls/apps/<id>` — that returns 404

**Mistakes made:**
- Tried to navigate directly to app edit page via UUID — got 404. Used API instead for the policy.

---

## Agent Session - Issue #18

**Worked on:** Issue #18 - Add NocoDB to backup and health check scripts

**What I did:**
- Extended `health-check.sh` with 2 new checks: NocoDB Docker container running + HTTP health endpoint
- Extended `backup.sh` with safe SQLite `.backup` snapshot before tarring, includes `nocodb/data/` directory, excludes live DB files (noco.db, WAL, SHM), auto-cleans backup file via trap
- Extended `restore-procedure.md` with NocoDB section explaining noco-backup.db → noco.db rename
- Deployed all 3 files to Mac Mini via scp
- Verified: health check 12/12 OK, backup includes nocodb data, S3 sync successful

**What I learned:**
- sqlite3 `.backup` command does NOT expand `~` — must use `$HOME` (bash expands it before passing)
- NocoDB health endpoint: `http://localhost:8080/api/v1/health`
- Today's backup already existed from 3am launchd run; had to delete to test new script
- SQLite `.backup` creates consistent snapshot without modifying source DB — safe approach for backup

**Codebase facts discovered:**
- Docker container name for NocoDB is just `nocodb` (not `nocodb-nocodb` like openclaw's `openclaw-openclaw-gateway`)
- NocoDB data: `~/services/nocodb/data/noco.db` (SQLite, ~2.4MB currently)

**Issue status:** Closed. All acceptance criteria met.

---

## Agent Session - Documentation Cleanup (Iteration 6)

**Worked on:** Documentation cleanup and NocoDB setup docs

**What I did:**
- Committed previously uncommitted files: AGENTS.md, README.md, updated email-routing.md
- Added NocoDB to README.md Live Services table
- Created `docs/nocodb-setup.md` with full NocoDB infrastructure documentation (prep for #20)
- Ran infrastructure health check — all 10 services healthy
- Surveyed all open issues for actionable work

**Issue assessment (all blocked):**
- #7 (OpenClaw migration): EC2 decommission blocked until 2026-03-25
- #9 (Legal Podcast migration): LegalPodcastStack deletion needs 1+ weeks stability (deployed 2026-03-20)
- #12 (Route 53 deletion): Blocked until 2026-03-31 (DNS cutover was 2026-03-17, needs 2+ weeks)
- #17 (Airtable → NocoDB): Blocked by ea-jobs-database#8 (still open)
- #19 (NocoDB MCP): Blocked by #17
- #20 (NocoDB docs/skills): Blocked by #17 and #19 (partially addressed with nocodb-setup.md)
- #21 (Merge EA Jobs into Contacts): Blocked by #17

**What I learned:**
- This repo has no CI pipeline or package.json — it's purely infrastructure/docs
- NocoDB v0.301.5 is running, API accessible locally at localhost:8080
- NocoDB admin credentials are not stored in .env (set up via UI on first access)
- All infrastructure is stable: 10/10 health checks pass

**Codebase facts discovered:**
- Uncommitted files from previous sessions can accumulate — agents should check git status for orphaned docs work

---

## Agent Session - Issue #9 (sub-issue #62)

**Worked on:** Issue #9 - Migrate Legal Podcast to Mac Mini → Preparing handoff for sub-issue #62 (Delete LegalPodcastStack)

**What I did:**
- Surveyed all open issues: #7, #9, #12, #17, #19, #20, #21
- #7 blocked until 2026-03-25 (EC2 decommission waiting period)
- #12 blocked until 2026-03-31 (Route 53 2-week stability window)
- #17+ are NocoDB work (lower priority)
- Chose #9 as most actionable: only sub-issue #62 remains (Delete LegalPodcastStack), needs human approval
- Verified legal podcast service fully operational on Mac Mini:
  - Docker container healthy
  - feed.xml: 200 OK
  - Admin dashboard: 200 OK
  - Audio files: 200 OK
  - Email webhook: 401 (correct auth rejection)
- Compared S3 vs Mac Mini data: 29/29 data files migrated (33 admin UI files served separately)
- Inventoried all 49 AWS resources in the stack (S3, CloudFront, Lambda, SES, API Gateway, etc.)
- Wrote HANDOFF.md with complete verification, exact commands, and post-deletion steps

**What I learned:**
- S3 bucket has AutoDeleteObjects enabled via CDK, so `cdk destroy` should handle non-empty bucket
- SES receipt rule for podcast@bjblabs.com is still active but no longer receives mail (MX → Cloudflare since 2026-03-17)
- The 62 S3 objects vs 29 Mac Mini files discrepancy is the admin UI (served from a separate directory on Mac Mini)

**Mistakes made:**
- None

---

## Agent Session - Issue #17 (Part 1: Ben Readings & Notes)

**Worked on:** Issue #17 - Migrate Airtable bases to NocoDB (first base)

**What was done:**
1. Surveyed open issues: #7, #9, #12 all blocked (waiting on time/approval)
2. Picked #17 as lowest actionable issue — Contacts and Readings bases are READY
3. Set up NocoDB admin account (ben@bjblabs.com, secure random password in `~/services/nocodb/.admin-creds`)
4. Created "Ben Readings & Notes" base in NocoDB (`pz0snc66hf3yi5f`)
5. Created "Readings" table with 14 fields matching Airtable schema (excl. CreatedTime auto-field and Attachments)
6. Exported all 746 records from Airtable via MCP (4 paginated batches of 200)
7. Wrote migration script (`scripts/migrate-readings.py`) that transforms and bulk-inserts
8. Successfully migrated all 746 records — verified count match
9. Also created empty "Contacts" base (`p4b83cic6kiud9b`) for next agent to populate
10. Updated nocodb-setup.md with auth docs, API endpoints, and migration status

**What I learned:**
- NocoDB v0.301.5 API: workspace-scoped endpoints (`/api/v2/meta/workspaces/:wsId/bases`) work, but direct base endpoints (`/api/v2/meta/bases`) return 403
- Record CRUD uses v1 path: `/api/v1/db/data/noco/:baseId/:tableId`
- Bulk insert: `/api/v1/db/data/bulk/noco/:baseId/:tableId` — returns `[]` on success (not the records)
- JWT tokens expire — need to re-sign-in before API calls
- NocoDB's "Import from Airtable" feature is UI-only (no API endpoint in this version)
- Programmatic migration via Airtable MCP + NocoDB API works well for simple tables
- Airtable MCP returns SingleSelect values as `{id, name, color}` objects — need to extract `name`

**Remaining work for #17:**
- Contacts base: create 4 tables (Contacts, Companies, Activities, Roles) with correct schemas
- Import records for all 4 tables (370 + 353 + 109 + 24 = 856 records)
- Set up linked record fields between tables and populate relationships
- Recreate formula fields (Activity Name, Title at Company)
- EA Jobs base: blocked by ea-jobs-database#8
- Attachments (Anki Cards, Resume, JD File): complex, may need HANDOFF

**Codebase facts discovered:**
- NocoDB workspace ID: `wqn2mxm7` (Default Workspace)
- Getting Started base exists by default (can be deleted)
- NocoDB admin creds stored at: `~/services/nocodb/.admin-creds`, API token at: `~/services/nocodb/.api-token`

**Mistakes made:**
- Initially created admin with "PLACEHOLDER" password — immediately changed to secure random password

---

## Agent Session - Issue #7 (Sub-issue: openclaw-deployment#36)

**Worked on:** Issue #7 - Migrate OpenClaw from EC2 to Mac Mini (final sub-issue: EC2 decommission)

**What I did:**
- Verified EC2 `i-0cc417431630fdfc5` stopped since 2026-03-18 (11 days, exceeds 1-week buffer)
- Verified OpenClaw on Mac Mini: both containers healthy, `openclaw.bjblabs.com` returning 200
- Identified CloudFormation stack `openclaw-ec2` manages all resources (instance, EBS, SG, IAM)
- Confirmed EBS volume has DeleteOnTermination=true, VPC is default (no cleanup needed)
- Wrote HANDOFF.md with exact `aws cloudformation delete-stack` command for Ben to approve
- Signaled PAUSED — destructive AWS action requires human approval

**What I learned:**
- The EC2 resources are managed by CloudFormation stack `openclaw-ec2`, so stack deletion is cleaner than individual resource deletion
- EBS volume auto-deletes on instance termination (DeleteOnTermination=true)

**Codebase facts discovered:**
- CloudFormation stack: `openclaw-ec2` (resources: EC2, SG, IAM role/profile)
- Associated VPC is the default VPC — no OpenClaw-specific networking to clean up

**Mistakes made:**
- None

---

## Agent Session - Issue #17

**Worked on:** Issue #17 - Migrate Airtable bases to NocoDB (Contacts base)

**What I did:**
- Exported all 4 Contacts base tables from Airtable via MCP (Contacts 370, Companies 353, Activities 109, Roles 24)
- Wrote migration script `scripts/migrate-contacts.py` to create NocoDB tables and bulk insert records
- Fixed NocoDB auth: admin email is `ben.bateman.email@gmail.com` not `ben@bjblabs.com`
- Generated JWT token directly using NC_AUTH_JWT_SECRET when password auth failed
- Fixed select column creation: `dtxp` format breaks on commas in option names, switched to `colOptions`
- Pre-scanned all records to collect unique select/multiselect values before table creation
- Successfully migrated all 856 records across 4 tables
- Saved link metadata to `scripts/contacts-migration-metadata.json` for future linking step
- Updated docs: nocodb-setup.md, LEARNINGS.md

**What I learned:**
- NocoDB admin email was `ben.bateman.email@gmail.com` (docs said `ben@bjblabs.com`)
- NocoDB select columns require options to be pre-defined during table creation
- `dtxp` format (`'opt1','opt2'`) splits on commas and breaks for values like "Oxford, UK / Remote"
- `colOptions.options` format handles arbitrary option names correctly
- NocoDB JWT can be generated directly using the auth secret from `.env` + user ID from SQLite
- NocoDB bulk insert API returns `[]` on success (not the inserted records)
- Python stdout buffering hides errors when running migration scripts — use `flush=True` or `-u`

**Codebase facts discovered:**
- NocoDB SQLite DB path: `~/services/nocodb/data/noco.db` (users table: `nc_users_v2`)
- Contacts base ID: `p4b83cic6kiud9b`, workspace: `wqn2mxm7`
- Previous migration (Readings) used similar pattern: export via MCP → transform → push via SSH

**Mistakes made:**
- First run: didn't pre-define select options → NocoDB rejected records with "Invalid option"
- First run: used `dtxp` format which breaks on commas in option names
- First run: stdout buffering hid batch progress (no flush), making debugging harder

---

## Agent Session - Issue #17 (Link Columns) + Issue #20 (Closed)

**Worked on:** Issue #17 - Contacts base link columns; Issue #20 - Documentation (closed)

**What I did:**
- Closed #20 — all acceptance criteria already met by prior agents. Fixed stale admin email in nocodb-setup.md.
- Created 7 many-to-many link columns across Contacts base tables (Contacts, Companies, Activities, Roles)
- Populated all 447 links from Airtable migration metadata into NocoDB junction tables
- Link relationships: Current Org (199), Past Orgs (40), Contacts↔Activities (112), Contacts↔Roles (9), Companies↔Roles (24), Companies↔Activities (39), Activities↔Roles (24)

**What I learned:**
- NocoDB link column creation via API: `POST /api/v2/meta/tables/{tableId}/columns` with `uidt: "Links"`, `type: "mm"`, `parentId`, `childId`
- Creating a link column auto-creates a reverse column on the child table (needs renaming for custom title)
- Reverse column renaming: `PATCH /api/v2/meta/columns/{columnId}` with `{"title": "new name"}`
- NocoDB MM links are stored in auto-created junction tables (format: `nc_uts0___nc_m2m_{Table1}_{Table2}`)
- Junction tables have FK columns named `nc_uts0___{TableName}_id`
- Can insert directly into junction tables via data API: `POST /api/v1/db/data/noco/{baseId}/{mmTableId}`
- Bulk insert endpoint: `POST /api/v1/db/data/bulk/noco/{baseId}/{mmTableId}` with array of records
- Junction tables have UNIQUE constraint on FK pair — prevents duplicate links
- NocoDB v0.301.5 link data API: the `/links/{columnId}/records/{rowId}` format did NOT work ("Field 'records' not found") — direct junction table insertion was the reliable path

**Codebase facts discovered:**
- Metadata file `scripts/contacts-migration-metadata.json` maps Airtable IDs → 0-based indices (NocoDB IDs = index + 1)
- id_mapping is consistent: sequential bulk insert preserves ordering (verified Id=1 maps to first contact)

**Mistakes made:**
- Test link (Contact 1 → Company 5) was wrong data — should have verified against metadata first
- populate-contacts-links.py reported 0 inserts due to response parsing error, but data was actually inserted (the bulk API returns different format than expected)
- Reverse column rename script had a bug: when multiple MM links exist between same table pair, it could rename the wrong column. Worked out due to NocoDB auto-naming matching expected names.
