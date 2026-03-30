#!/usr/bin/env python3
"""Migrate EA Jobs records into Job Postings table in Contacts base.

1. Creates new Company records for unmatched EA Jobs orgs
2. Inserts Job Posting records (from EA Jobs data)
3. Links each Job Posting to its Company via junction table
4. Enriches existing Company records with EA Jobs metadata

Run on Mac Mini: python3 /tmp/migrate-job-postings.py

Part of issue #21: Merge EA Jobs into Contacts database.
"""

import json
import os
import urllib.request
import urllib.parse
import subprocess
import sys

NOCODB_URL = "http://localhost:8080"
CONTACTS_BASE = "p4b83cic6kiud9b"
EA_JOBS_BASE = "pxo2rnpo3ud4ulk"
EA_JOBS_TABLE = "mim7su9us6cxvju"
JOB_POSTINGS_TABLE = "m78buufldaz365j"
COMPANIES_TABLE = "mk6e9lanspt27rg"
JUNCTION_TABLE = "meyb0jdy3yd9pyp"
JUNCTION_JP_COL = "nc_uts0___Job Postings_id"
JUNCTION_CO_COL = "nc_uts0___Companies_id"
MATCH_REPORT_PATH = "/tmp/match_report.json"
BATCH_SIZE = 100

# Confirmed matches from human review of MATCH_REPORT.md
# These were flagged as medium-confidence by the algorithm but verified correct
CONFIRMED_MATCHES = {
    "Gi Effektivt": 111,
    "Good Impressions Media": 237,
    "Survival and Flourishing": 147,
    "UK Government, AI Security Institute": 65,
    "Model Evaluation and Threat Research": 163,
    "MATS Research": 14,
    "Evidence Action": 295,
}

# Fields to copy from EA Jobs → Job Postings (src → dst)
FIELD_MAP = {
    "git_id": "EA Jobs git_id",
    "Title": "Title",
    "Source": "Source",
    "Source URL": "Source URL",
    "Status": "Status",
    "Location Type": "Location Type",
    "Cities": "Cities",
    "Salary Min": "Salary Min",
    "Salary Max": "Salary Max",
    "Salary Currency": "Salary Currency",
    "Salary Period": "Salary Period",
    "Posted Date": "Posted Date",
    "Deadline": "Deadline",
    "Date Added": "Date Added",
    "Tags": "Tags",
    "Confidence": "Confidence",
    "Notes": "Notes",
    "Job Description": "Job Description",
}


def get_token():
    with open(os.path.expanduser("~/services/nocodb/.api-token")) as f:
        return f.read().strip()


def refresh_token():
    pwd = subprocess.check_output(
        "grep Password ~/services/nocodb/.admin-creds | cut -d' ' -f4",
        shell=True,
    ).decode().strip()
    data = json.dumps({"email": "ben.bateman.email@gmail.com", "password": pwd}).encode()
    req = urllib.request.Request(
        f"{NOCODB_URL}/api/v1/auth/user/signin",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    token_data = json.loads(resp.read())
    token = token_data["token"]
    with open(os.path.expanduser("~/services/nocodb/.api-token"), "w") as f:
        f.write(token)
    return token


def api_get(path, token, params=None):
    url = f"{NOCODB_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"xc-auth": token})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return None
        raise


def api_post(path, token, data):
    url = f"{NOCODB_URL}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"xc-auth": token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"  HTTP {e.code}: {err_body[:500]}")
        raise


def api_patch(path, token, data):
    url = f"{NOCODB_URL}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=body, method="PATCH",
        headers={"xc-auth": token, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_all(base_id, table_id, token, fields=None):
    """Fetch all records with pagination."""
    records = []
    offset = 0
    while True:
        params = {"limit": 200, "offset": offset}
        if fields:
            params["fields"] = fields
        data = api_get(f"/api/v1/db/data/noco/{base_id}/{table_id}", token, params)
        if data is None:
            return None
        records.extend(data.get("list", []))
        if data.get("pageInfo", {}).get("isLastPage", True):
            break
        offset += 200
    return records


def bulk_insert(base_id, table_id, records, token, label="records", batch_size=None):
    """Insert records in batches, return total inserted."""
    bs = batch_size or BATCH_SIZE
    total = len(records)
    batches = (total + bs - 1) // bs
    for i in range(0, total, bs):
        batch = records[i:i + bs]
        batch_num = i // bs + 1
        result = api_post(
            f"/api/v1/db/data/bulk/noco/{base_id}/{table_id}", token, batch
        )
        if isinstance(result, dict) and "error" in result:
            print(f"  ERROR batch {batch_num}: {result}")
            sys.exit(1)
        print(f"  {label} batch {batch_num}/{batches} ({len(batch)} records)")
    return total


def build_org_map(match_report):
    """Build org name → Company NocoDB ID mapping from match data."""
    org_map = {}
    for m in match_report.get("exact_matches", []):
        org_map[m["ea_org"]] = m["matched_company_id"]
    for m in match_report.get("high_confidence_matches", []):
        org_map[m["ea_org"]] = m["matched_company_id"]
    org_map.update(CONFIRMED_MATCHES)
    return org_map


def main():
    # Get token
    token = get_token()
    test = api_get("/api/v1/health", token)
    if test is None:
        print("Token expired, refreshing...")
        token = refresh_token()

    # Load match report
    with open(MATCH_REPORT_PATH) as f:
        match_report = json.load(f)
    org_map = build_org_map(match_report)
    print(f"Org mapping: {len(org_map)} orgs → existing companies")

    # Collect enrichment data from match report (for existing companies)
    enrichment = {}
    for m in match_report.get("exact_matches", []) + match_report.get("high_confidence_matches", []):
        cid = m["matched_company_id"]
        enrichment[cid] = {
            "website": m.get("ea_website"),
            "hq": m.get("ea_hq"),
            "existing_website": m.get("matched_company_website"),
        }

    # === Phase 1: Fetch EA Jobs records ===
    print("\nPhase 1: Fetching EA Jobs records...")
    ea_jobs = fetch_all(EA_JOBS_BASE, EA_JOBS_TABLE, token)
    if ea_jobs is None:
        token = refresh_token()
        ea_jobs = fetch_all(EA_JOBS_BASE, EA_JOBS_TABLE, token)
    print(f"  {len(ea_jobs)} records")

    # === Phase 2: Create new Company records for unmatched orgs ===
    print("\nPhase 2: Creating new Company records for unmatched orgs...")

    # First, fetch existing companies to avoid duplicates
    print("  Fetching existing Companies...")
    companies = fetch_all(CONTACTS_BASE, COMPANIES_TABLE, token, "Id,Title,Name,Website")
    if companies is None:
        token = refresh_token()
        companies = fetch_all(CONTACTS_BASE, COMPANIES_TABLE, token, "Id,Title,Name,Website")
    name_to_id = {}
    for c in companies:
        for field in ("Title", "Name"):
            val = (c.get(field) or "").strip()
            if val:
                name_to_id[val] = c["Id"]
    print(f"  {len(companies)} companies, {len(name_to_id)} unique names")

    # Find orgs that still need Company records
    unmatched_orgs = {}
    for job in ea_jobs:
        org = job.get("Organization", "").strip()
        if not org or org.startswith("Various"):
            continue
        if org not in org_map and org not in name_to_id and org not in unmatched_orgs:
            unmatched_orgs[org] = {
                "website": job.get("Org Website"),
                "hq": job.get("Org HQ"),
                "cause_areas": job.get("Org Cause Areas"),
            }
        if org in unmatched_orgs:
            meta = unmatched_orgs[org]
            if not meta["website"] and job.get("Org Website"):
                meta["website"] = job["Org Website"]
            if not meta["hq"] and job.get("Org HQ"):
                meta["hq"] = job["Org HQ"]
            if not meta["cause_areas"] and job.get("Org Cause Areas"):
                meta["cause_areas"] = job["Org Cause Areas"]

    new_companies = []
    for org_name, meta in unmatched_orgs.items():
        record = {"Title": org_name, "Name": org_name}
        if meta.get("website"):
            record["Website"] = meta["website"]
        if meta.get("hq"):
            record["Location"] = meta["hq"]
        new_companies.append(record)

    if new_companies:
        bulk_insert(CONTACTS_BASE, COMPANIES_TABLE, new_companies, token, "Companies")
        print(f"  Created {len(new_companies)} new Company records")
        # Re-fetch to update mapping
        companies = fetch_all(CONTACTS_BASE, COMPANIES_TABLE, token, "Id,Title,Name,Website")
        if companies is None:
            token = refresh_token()
            companies = fetch_all(CONTACTS_BASE, COMPANIES_TABLE, token, "Id,Title,Name,Website")
        name_to_id = {}
        for c in companies:
            for field in ("Title", "Name"):
                val = (c.get(field) or "").strip()
                if val:
                    name_to_id[val] = c["Id"]
    else:
        print("  No new companies needed")

    # Update org_map: add all orgs that map to a company by name
    for job in ea_jobs:
        org = job.get("Organization", "").strip()
        if org and org not in org_map and org in name_to_id:
            org_map[org] = name_to_id[org]
    print(f"  Total org mappings: {len(org_map)}")

    # === Phase 3: Check Job Postings table is empty ===
    jp_check = api_get(
        f"/api/v1/db/data/noco/{CONTACTS_BASE}/{JOB_POSTINGS_TABLE}", token, {"limit": 1}
    )
    if jp_check and jp_check.get("pageInfo", {}).get("totalRows", 0) > 0:
        print("\nERROR: Job Postings table already has records. Aborting.")
        sys.exit(1)

    # === Phase 4: Insert Job Postings ===
    print(f"\nPhase 3: Inserting {len(ea_jobs)} Job Postings...")
    job_postings = []
    for job in ea_jobs:
        record = {}
        for src, dst in FIELD_MAP.items():
            val = job.get(src)
            if val is not None and val != "" and val != []:
                record[dst] = val
        job_postings.append(record)

    # Use smaller batches — Job Description field makes records very large
    bulk_insert(CONTACTS_BASE, JOB_POSTINGS_TABLE, job_postings, token,
                "Job Postings", batch_size=25)

    # Verify count
    jp_verify = api_get(
        f"/api/v1/db/data/noco/{CONTACTS_BASE}/{JOB_POSTINGS_TABLE}", token, {"limit": 1}
    )
    jp_total = jp_verify.get("pageInfo", {}).get("totalRows", 0) if jp_verify else 0
    print(f"  Inserted: {jp_total} (expected {len(job_postings)})")
    if jp_total != len(job_postings):
        print("  WARNING: Count mismatch!")

    # === Phase 5: Link Job Postings to Companies ===
    print("\nPhase 4: Linking Job Postings to Companies...")

    # Fetch all Job Postings to get their NocoDB IDs (keyed by git_id)
    all_jps = fetch_all(CONTACTS_BASE, JOB_POSTINGS_TABLE, token, "Id,EA Jobs git_id")
    if all_jps is None:
        token = refresh_token()
        all_jps = fetch_all(CONTACTS_BASE, JOB_POSTINGS_TABLE, token, "Id,EA Jobs git_id")
    gitid_to_jpid = {}
    for jp in all_jps:
        gid = (jp.get("EA Jobs git_id") or "").strip()
        if gid:
            gitid_to_jpid[gid] = jp["Id"]
    print(f"  {len(gitid_to_jpid)} Job Postings with git_id")

    # Build junction records
    junction = []
    linked = 0
    unlinked_no_company = 0
    unlinked_no_jp = 0
    for job in ea_jobs:
        org = (job.get("Organization") or "").strip()
        gid = (job.get("git_id") or "").strip()
        company_id = org_map.get(org)
        jp_id = gitid_to_jpid.get(gid)
        if not jp_id:
            unlinked_no_jp += 1
            continue
        if not company_id:
            unlinked_no_company += 1
            continue
        junction.append({
            JUNCTION_CO_COL: company_id,
            JUNCTION_JP_COL: jp_id,
        })
        linked += 1

    print(f"  Links: {linked}, no company: {unlinked_no_company}, no JP: {unlinked_no_jp}")
    if junction:
        bulk_insert(CONTACTS_BASE, JUNCTION_TABLE, junction, token, "Junction")

    # === Phase 6: Enrich existing Companies ===
    print("\nPhase 5: Enriching matched Companies with EA Jobs metadata...")
    enriched = 0
    for cid, meta in enrichment.items():
        updates = {}
        # Add website if company doesn't have one
        if meta.get("website") and not meta.get("existing_website"):
            updates["Website"] = meta["website"]
        # Add HQ as Location
        if meta.get("hq"):
            # Check if company already has Location
            for c in companies:
                if c["Id"] == cid:
                    if not c.get("Location"):
                        updates["Location"] = meta["hq"]
                    break
        if updates:
            try:
                api_patch(
                    f"/api/v1/db/data/noco/{CONTACTS_BASE}/{COMPANIES_TABLE}/{cid}",
                    token, updates,
                )
                enriched += 1
            except Exception as e:
                print(f"  Failed to enrich company {cid}: {e}")
    print(f"  Enriched {enriched} companies")

    # === Summary ===
    print("\n" + "=" * 50)
    print("Migration complete!")
    print(f"  Job Postings created: {jp_total}")
    print(f"  New Companies created: {len(new_companies)}")
    print(f"  Company links created: {linked}")
    print(f"  Companies enriched: {enriched}")
    print(f"  Unlinked (no company): {unlinked_no_company}")
    print(f"  Unlinked (no JP match): {unlinked_no_jp}")
    print("=" * 50)


if __name__ == "__main__":
    main()
