#!/usr/bin/env python3
"""
Fuzzy match EA Jobs organizations against Contacts Companies.
Runs on the Mac Mini with direct NocoDB access at localhost:8080.

Part of issue #21: Merge EA Jobs into Contacts database.
"""

import json
import urllib.request
import urllib.parse
from difflib import SequenceMatcher
from collections import defaultdict

NOCODB_URL = "http://localhost:8080"
CONTACTS_BASE = "p4b83cic6kiud9b"
EA_JOBS_BASE = "pxo2rnpo3ud4ulk"
# Table IDs (NocoDB API requires IDs, not titles)
COMPANIES_TABLE = "mk6e9lanspt27rg"
JOBS_TABLE = "mim7su9us6cxvju"

def get_token():
    """Read API token from file."""
    with open("/Users/ben/services/nocodb/.api-token") as f:
        return f.read().strip()

def refresh_token():
    """Get a fresh token via sign-in."""
    import subprocess
    pwd = subprocess.check_output(
        "grep Password /Users/ben/services/nocodb/.admin-creds | cut -d' ' -f4",
        shell=True
    ).decode().strip()
    data = json.dumps({"email": "ben.bateman.email@gmail.com", "password": pwd}).encode()
    req = urllib.request.Request(
        f"{NOCODB_URL}/api/v1/auth/user/signin",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    token = json.loads(resp.read())["token"]
    with open("/Users/ben/services/nocodb/.api-token", "w") as f:
        f.write(token)
    return token

def api_get(path, token, params=None):
    """Make authenticated GET request to NocoDB."""
    url = f"{NOCODB_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"xc-auth": token})
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return None  # token expired
        raise

def fetch_all_records(base_id, table_id, fields, token):
    """Fetch all records from a table, handling pagination."""
    records = []
    offset = 0
    limit = 200
    while True:
        data = api_get(
            f"/api/v1/db/data/noco/{base_id}/{table_id}",
            token,
            {"fields": fields, "limit": limit, "offset": offset}
        )
        if data is None:
            return None  # token expired
        records.extend(data.get("list", []))
        page_info = data.get("pageInfo", {})
        if page_info.get("isLastPage", True):
            break
        offset += limit
    return records

def normalize(name):
    """Normalize org name for comparison."""
    name = name.strip().lower()
    # Remove common suffixes/prefixes
    for suffix in [" inc", " inc.", " llc", " ltd", " ltd.", " co.", " corp", " corp."]:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    return name

def similarity(a, b):
    """Compute similarity ratio between two strings."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def find_best_match(ea_org, companies):
    """Find best matching company for an EA Jobs org name."""
    best_score = 0
    best_match = None
    for company in companies:
        score = similarity(ea_org, company["Name"])
        if score > best_score:
            best_score = score
            best_match = company
    return best_match, best_score

def main():
    # Get token
    token = get_token()

    # Test token
    test = api_get("/api/v1/health", token)
    if test is None:
        print("Token expired, refreshing...")
        token = refresh_token()

    # Fetch Companies
    print("Fetching Companies from Contacts base...", flush=True)
    companies = fetch_all_records(CONTACTS_BASE, COMPANIES_TABLE, "Id,Name,Website,Location,Org Type,Career Interest", token)
    if companies is None:
        token = refresh_token()
        companies = fetch_all_records(CONTACTS_BASE, COMPANIES_TABLE, "Id,Name,Website,Location,Org Type,Career Interest", token)
    print(f"  Found {len(companies)} companies", flush=True)

    # Fetch EA Jobs orgs
    print("Fetching Jobs from EA Jobs base...", flush=True)
    jobs = fetch_all_records(EA_JOBS_BASE, JOBS_TABLE, "Id,Organization,Org Website,Org HQ,Org Cause Areas", token)
    if jobs is None:
        token = refresh_token()
        jobs = fetch_all_records(EA_JOBS_BASE, JOBS_TABLE, "Id,Organization,Org Website,Org HQ,Org Cause Areas", token)
    print(f"  Found {len(jobs)} job records")

    # Extract unique EA Jobs organizations
    ea_orgs = {}  # name -> {website, hq, cause_areas, job_count}
    for job in jobs:
        org = job.get("Organization", "").strip()
        if not org or org.startswith("Various"):
            continue
        if org not in ea_orgs:
            ea_orgs[org] = {
                "website": job.get("Org Website"),
                "hq": job.get("Org HQ"),
                "cause_areas": job.get("Org Cause Areas"),
                "job_count": 0
            }
        ea_orgs[org]["job_count"] += 1
        # Fill in missing metadata from other records
        if not ea_orgs[org]["website"] and job.get("Org Website"):
            ea_orgs[org]["website"] = job["Org Website"]
        if not ea_orgs[org]["hq"] and job.get("Org HQ"):
            ea_orgs[org]["hq"] = job["Org HQ"]
        if not ea_orgs[org]["cause_areas"] and job.get("Org Cause Areas"):
            ea_orgs[org]["cause_areas"] = job["Org Cause Areas"]

    print(f"  Unique organizations: {len(ea_orgs)}")

    # Build company name index (strip whitespace)
    for c in companies:
        if c.get("Name"):
            c["Name"] = c["Name"].strip()

    # Match each EA org against Companies
    exact_matches = []
    high_confidence = []   # >= 0.85
    medium_confidence = [] # >= 0.70
    low_confidence = []    # >= 0.55
    no_match = []          # < 0.55

    for org_name, org_info in sorted(ea_orgs.items()):
        best_company, score = find_best_match(org_name, companies)

        match_record = {
            "ea_org": org_name,
            "ea_website": org_info["website"],
            "ea_hq": org_info["hq"],
            "ea_cause_areas": org_info["cause_areas"],
            "ea_job_count": org_info["job_count"],
            "matched_company": best_company["Name"] if best_company else None,
            "matched_company_id": best_company["Id"] if best_company else None,
            "matched_company_website": best_company.get("Website") if best_company else None,
            "confidence": round(score, 3),
        }

        if score == 1.0 or normalize(org_name) == normalize(best_company["Name"] if best_company else ""):
            exact_matches.append(match_record)
        elif score >= 0.85:
            high_confidence.append(match_record)
        elif score >= 0.70:
            medium_confidence.append(match_record)
        elif score >= 0.55:
            low_confidence.append(match_record)
        else:
            no_match.append(match_record)

    # Build report
    report = {
        "summary": {
            "total_companies": len(companies),
            "total_ea_jobs_records": len(jobs),
            "unique_ea_orgs": len(ea_orgs),
            "exact_matches": len(exact_matches),
            "high_confidence": len(high_confidence),
            "medium_confidence": len(medium_confidence),
            "low_confidence": len(low_confidence),
            "no_match_new_orgs": len(no_match),
        },
        "exact_matches": exact_matches,
        "high_confidence_matches": high_confidence,
        "medium_confidence_review": medium_confidence,
        "low_confidence_review": low_confidence,
        "no_match_new_orgs": no_match,
    }

    # Output as JSON
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
