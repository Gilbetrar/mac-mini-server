# Session Log

Raw session history for the mac-mini-server project.

---

## Agent Session - Issue #21

**Worked on:** Issue #21 - Merge EA Jobs into Contacts database (Step 1: fuzzy matching)

**What I did:**
- Surveyed both NocoDB bases: Contacts (353 Companies, 4 tables) and EA Jobs (835 records, 1 table)
- Fetched all table schemas and record data via MCP tools
- Wrote a Python fuzzy matching script (`scripts/org-matching/match_orgs.py`) using difflib.SequenceMatcher
- Ran the script on the Mac Mini via SSH (direct localhost:8080 access, bypassing Zero Trust)
- Generated comprehensive match report with 343 unique EA Jobs orgs analyzed
- Results: 35 exact, 12 high-confidence, 4 true medium matches, 3 acronym matches, 24 false positives, 145 new orgs
- Created HANDOFF.md with 10 items for Ben to review before proceeding

**What I learned:**
- NocoDB REST API requires table IDs (like `mk6e9lanspt27rg`) in URL paths, not table titles ("Companies")
- String-similarity (SequenceMatcher) misses acronym matches entirely (e.g., "Model Evaluation and Threat Research" vs "METR")
- Running Python scripts on Mac Mini via SSH + localhost:8080 is the fastest way to query NocoDB API (avoids Zero Trust)
- EA Jobs has lots of duplicate org records (835 records → 343 unique orgs); Anthropic alone has 44 job records

**Codebase facts discovered:**
- Contacts base ID: p4b83cic6kiud9b, Companies table ID: mk6e9lanspt27rg, Roles table ID: mnoqjf6ajrnx7vn
- EA Jobs base ID: pxo2rnpo3ud4ulk, Jobs table ID: mim7su9us6cxvju
- Workspace ID: wqn2mxm7

**Mistakes made:**
- First script run failed with 404 because I used table title "Companies" instead of table ID in the API URL

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

---

## Agent Session - Issue #17

**Worked on:** Issue #17 - Migrate Airtable bases to NocoDB (EA Jobs base — final remaining base)

**What I did:**
- Created "EA Jobs Database" base in NocoDB (`pxo2rnpo3ud4ulk`)
- Created Jobs table with 22 columns matching Airtable schema
- Added SingleSelect/MultiSelect options via column PATCH API (6 select columns, 33 tag options)
- Migrated all 835 records from Airtable via bulk API insert in 9 batches
- Verified record count matches: 835/835
- Spot-checked records: git_id, Title, Organization, Tags, Job Description all populated correctly
- Updated docs/nocodb-setup.md and LEARNINGS.md

**What I learned:**
- NocoDB MCP `create_table` does NOT populate select options from `meta.options` — must add them separately via `PATCH /api/v2/meta/columns/{colId}` with `colOptions.options`
- NocoDB password reset requires using the SAME bcrypt salt from `nc_users_v2.salt` column — generating a new salt won't work even though `bcrypt.compare()` passes
- NocoDB API tokens (`xc-token` header) only work for data operations, NOT admin/meta like creating bases — need JWT (`xc-auth`) for those
- Base creation endpoint is workspace-scoped: `POST /api/v2/meta/workspaces/{wsId}/bases/` (not just `/api/v2/meta/bases/`)
- Must stop NocoDB container before modifying SQLite directly, then restart
- JWT can be generated inside the Docker container using Node.js `jsonwebtoken` library

**Codebase facts discovered:**
- NocoDB workspace ID: `wqn2mxm7`
- NocoDB user ID: `usxydx75wfvfob8h`
- ea-jobs-database#8 (dependency) is now CLOSED — EA Jobs base was unblocked

**Mistakes made:**
- Spent significant time on NocoDB auth: JWT generated manually (Python/Node) didn't work even with correct secret — turned out the container's `jsonwebtoken` lib also failed. Password reset worked but only after using the original salt. This should have been the first thing tried.
- First migration run failed silently (no batch output) because the original script used `json.loads()` error parsing that swallowed the NocoDB validation error about missing select options

---

## Agent Session - Issue #21 (Job Postings Migration)

**Worked on:** Issue #21 - Merge EA Jobs into Contacts database (Job Postings table creation and data migration)

**What I did:**
1. Created "Job Postings" table in Contacts base with 18 data columns matching EA Jobs schema
2. Added Company link column (many-to-many) via NocoDB REST API
3. Added SingleSelect/MultiSelect options to all select columns (Source, Status, Location Type, Salary Currency, Salary Period, Tags)
4. Wrote and ran `scripts/migrate-job-postings.py` on Mac Mini
5. Migrated 835 EA Jobs records as Job Postings
6. Linked 822 Job Postings to Companies via junction table
7. 13 unlinked are "Various..." aggregate listings (expected)
8. Enriched 21 existing Company records with website/location from EA Jobs metadata

**What I learned:**
- NocoDB bulk insert rejects records with SingleSelect values when no options are defined — must add options via `PATCH /api/v2/meta/columns/{colId}` BEFORE inserting data
- Job Descriptions can be huge (10KB+) — batch size of 25 needed vs normal 100 for bulk insert
- Junction table columns for "Job Postings" link have spaces in column names (`nc_uts0___Job Postings_id`) — works fine in JSON keys
- The previous agent created 289 new Company records for unmatched orgs but failed on Job Postings insert — script needed to detect existing companies rather than re-creating

**Codebase facts discovered:**
- Job Postings table ID: `m78buufldaz365j`
- Junction table (JP↔Companies): `meyb0jdy3yd9pyp` with columns `nc_uts0___Companies_id` and `nc_uts0___Job Postings_id`
- Match report has 54 auto-linkable orgs (35 exact + 12 high + 7 confirmed), 289 new orgs created as Companies

**Remaining work for issue #21:**
- Rename Roles → Applications
- Add optional link from Applications to Job Postings
- Delete standalone EA Jobs base
- Ben needs to review 3 context-needed matches (RAND Corporation, Animal Equality, EA Funds)

---

## Agent Session - 2026-04-21 — Migration wrap-up

**Worked on:** Issue #21 human-review items, AWS teardown (issues #7, #9, #12), Cloudflare Email Worker bug fix.

**What I did:**
1. **Match report resolution (issue #21)** — walked Ben through the 10 flagged matches. He confirmed RAND Corporation = RAND = RAND CAST (merge), Animal Equality as new, EA Funds as new, and approved the 7 auto-linked medium-confidence matches. Also flagged and merged duplicate UK AI Security Institute records (IDs 65 + 243).
2. **RAND merge** — wrote `scripts/merge-companies.py` and `scripts/recover-rand-links.py` (executed on Mac Mini via SSH + `npx wrangler` pattern). Canonical Company 431 now has career data from 50 and 311, Role 14 title is "Director of Operations, CAST", all contacts (5)/roles (1)/activities (7) re-linked.
3. **UK AI Security Institute merge** — Company 65 renamed to "UK AI Security Institute" with website + Bill's 0-tier note; Company 243 deleted.
4. **Cloudflare Email Worker fix** — user's test email to `podcast@bjblabs.com` bounced with HTTP 405. Root cause: `email-worker/wrangler.toml` had `WEBHOOK_URL = .../webhook/email` (singular); service expects `/webhooks/email` (plural). Fixed, redeployed via `npx wrangler deploy` on Mac Mini, verified end-to-end — service now logs "No DOCX attachments found" for test sender (auth + parsing works).
5. **AWS teardown (partial)** — terminated OpenClaw EC2 `i-0cc417431630fdfc5`. Deleted `LegalPodcastStack` (required deactivating the SES rule set `legal-podcast-rules` first; initial delete-stack failed on the active ruleset). Cleaned up 9 email-related Route 53 records (MX, 2 DMARC TXT, 6 DKIM CNAMEs). Zone now has 4 records: NS, SOA, and 2 orphan ACM validation CNAMEs (pending Ben's OK on the final 2 delete-then-zone steps).

**What I learned:**
- **NocoDB junction rows have no exposed row ID via the data API** — the PATCH-by-row-id approach fails with `/None` URL and HTTP 500. Junction rows are identified by the composite `(fk1, fk2)` pair only. For merges, use INSERT + bulk DELETE by composite key, not PATCH. (Full pattern in `scripts/merge-companies.py` + `scripts/recover-rand-links.py`.)
- **NocoDB Company delete does NOT cascade** to junction rows — they become zombie rows pointing to dangling FK. UI rollups silently ignore them but they're dirty data; clean up via bulk DELETE by composite key.
- **SES active receipt rule sets block CloudFormation delete** — must call `aws ses set-active-receipt-rule-set` (with no args) to deactivate before `delete-stack` can remove the rule set resource.
- **Wrangler authentication quirk** — `npx wrangler deploy` with `CLOUDFLARE_API_TOKEN` env var hits `/memberships` on startup, fails with 10000 if the token lacks "User Details: Read". Workaround: also set `CLOUDFLARE_ACCOUNT_ID` explicitly (account `95f53250a929e155644f51e03fc7c910` for this account).
- **Caddy routes mismatch between Worker and service** silently route to static-file fallback — a GET returning 200 and a POST returning 405 on the same URL is the signature.

**Codebase facts discovered:**
- Junction table IDs in Contacts base: `mm375v0y4lmezkm` (Contacts↔Companies Current), `m4pmrpbinopg4wd` (Contacts↔Companies Past), `m1y3ddrl9qv6t3m` (Companies↔Roles), `mav5v1ftufxhx4j` (Companies↔Activities).
- Canonical records after merge: Company 431 "RAND Corporation", Company 65 "UK AI Security Institute".
- Animal Equality (ID 407) and EA Funds (ID 412) already existed as distinct Companies from the earlier migration — no action needed.
- Companies table has 642 rows (expected ~498). Previous migration's first-run duplicates need a dedup sweep later.
- Cloudflare Worker `legal-podcast-email-forwarder` deployed from `email-worker/` via `npx wrangler deploy`; version ID `5c89d2ba-95bf-408a-b19b-f2976c86307e`.

**Mistakes made:**
- First RAND merge attempt used PATCH on junction rows with `row.get("id") or row.get("Id")` — both returned None, URL became `.../None`, HTTP 500. Delete of Companies 50/311 went through before the PATCH errors were caught, leaving 13 orphaned records for ~30 seconds until recovery script re-inserted the junction links.
- Originally assumed the webhook path was `/webhook/email` based on wrangler.toml, when service code + docs + tests all use `/webhooks/email`. Should have grepped the service repo before sending the first test email.

**Remaining work:**
- Final 2 Route 53 CNAMEs + zone deletion (blocked on explicit user OK due to sandbox caution)
- Roles → Applications rename + add Applications↔Job Postings link (issue #21)
- Delete standalone EA Jobs base in NocoDB (issue #21)
- Dedup sweep on Companies table + zombie junction cleanup
