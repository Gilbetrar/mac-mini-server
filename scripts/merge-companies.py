#!/usr/bin/env python3
"""Merge duplicate Company records in the Contacts base (issue #21 follow-up).

Usage:
  python3 scripts/merge-companies.py           # dry-run: prints planned changes
  python3 scripts/merge-companies.py --execute # performs the operations

Merges:
  RAND: canonical 431 (RAND Corporation). Sources: 50 (RAND CAST), 311 (Rand).
        - Role 14 title gets ", CAST" suffix to preserve subteam context.
  UKASI: canonical 65 (renamed to "UK AI Security Institute"). Source: 243.
         - 243 has no links, so this is enrich + delete.
"""
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import subprocess

NOCODB_URL = "http://localhost:8080"
CONTACTS_BASE = "p4b83cic6kiud9b"
COMPANIES_TABLE = "mk6e9lanspt27rg"
CONTACTS_TABLE = "mor9pdbxxz7i6gy"
ROLES_TABLE = "mnoqjf6ajrnx7vn"
ACTIVITIES_TABLE = "m3924zh9ss3wmdf"

MERGES = [
    {
        "label": "RAND",
        "canonical_id": 431,
        "rename": None,
        "enrich": {
            "Org Type": "EA,Policy",
            "Career Interest": "Interested",
            "Career Priority": "P3",
            "Career Track": "Grow inside EA",
            "Career change": "Lateral move",
            "Jobs Page": "https://www.rand.org/jobs.html",
            "Notes": "I should chat with Bill and actually get a pitch on this. Previously tracked as separate RAND/RAND CAST records; merged 2026-04-21.",
        },
        "sources": [50, 311],
        "role_title_updates": {14: "Director of Operations, CAST"},
    },
    {
        "label": "UK AI Security Institute",
        "canonical_id": 65,
        "rename": "UK AI Security Institute",
        "enrich": {
            "Name": "UK AI Security Institute",
            "Title": "UK AI Security Institute",
            "Website": "https://www.aisi.gov.uk/",
            "Notes": "Bill's 0-tier. UK government org. Renamed from 'AI Safety Institute' in 2025. Conducts model evaluations.",
            "Career Track": "Grow inside EA",
        },
        "sources": [243],
        "role_title_updates": {},
    },
]

DRY_RUN = "--execute" not in sys.argv


def get_token():
    with open(os.path.expanduser("~/services/nocodb/.api-token")) as f:
        return f.read().strip()


def refresh_token():
    pwd = subprocess.check_output(
        "grep Password ~/services/nocodb/.admin-creds | cut -d' ' -f4",
        shell=True,
    ).decode().strip()
    data = json.dumps(
        {"email": "ben.bateman.email@gmail.com", "password": pwd}
    ).encode()
    req = urllib.request.Request(
        f"{NOCODB_URL}/api/v1/auth/user/signin",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    token = json.loads(resp.read())["token"]
    with open(os.path.expanduser("~/services/nocodb/.api-token"), "w") as f:
        f.write(token)
    return token


def api(method, path, token, data=None, params=None):
    url = f"{NOCODB_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    body = json.dumps(data).encode() if data is not None else None
    headers = {"xc-auth": token}
    if body:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode() if e.fp else ""
        raise RuntimeError(
            f"HTTP {e.code} on {method} {path}: {err_body[:500]}"
        ) from e


def ensure_token():
    token = get_token()
    try:
        api(
            "GET",
            f"/api/v1/db/meta/projects/{CONTACTS_BASE}/tables",
            token,
            params={"includeM2M": "true"},
        )
        return token
    except RuntimeError as e:
        if "HTTP 401" in str(e):
            print("Token expired, refreshing...")
            return refresh_token()
        raise


def discover_junctions(token):
    """Find all M2M junction tables in the Contacts base."""
    result = api(
        "GET",
        f"/api/v1/db/meta/projects/{CONTACTS_BASE}/tables",
        token,
        params={"includeM2M": "true"},
    )
    junctions = {}
    for t in result.get("list", []):
        name = t.get("table_name", "")
        if "nc_m2m" in name:
            junctions[t["title"]] = {
                "id": t["id"],
                "table_name": name,
            }
    return junctions


def fetch_junction_rows(junction_id, company_col, company_id, token):
    params = {
        "limit": 500,
        "where": f"({company_col},eq,{company_id})",
    }
    result = api(
        "GET",
        f"/api/v1/db/data/noco/{CONTACTS_BASE}/{junction_id}",
        token,
        params=params,
    )
    return result.get("list", [])


def update_junction_row(junction_id, row_id, new_fields, token):
    return api(
        "PATCH",
        f"/api/v1/db/data/noco/{CONTACTS_BASE}/{junction_id}/{row_id}",
        token,
        data=new_fields,
    )


def delete_junction_row(junction_id, row_id, token):
    return api(
        "DELETE",
        f"/api/v1/db/data/noco/{CONTACTS_BASE}/{junction_id}/{row_id}",
        token,
    )


def check_junction_exists(junction_id, company_col, other_col, company_id, other_id, token):
    params = {
        "limit": 1,
        "where": f"({company_col},eq,{company_id})~and({other_col},eq,{other_id})",
    }
    result = api(
        "GET",
        f"/api/v1/db/data/noco/{CONTACTS_BASE}/{junction_id}",
        token,
        params=params,
    )
    return len(result.get("list", [])) > 0


def update_record(table_id, record_id, data, token):
    return api(
        "PATCH",
        f"/api/v1/db/data/noco/{CONTACTS_BASE}/{table_id}/{record_id}",
        token,
        data=data,
    )


def delete_record(table_id, record_id, token):
    return api(
        "DELETE",
        f"/api/v1/db/data/noco/{CONTACTS_BASE}/{table_id}/{record_id}",
        token,
    )


def relink_company(junction_id, company_col, other_col, source_id, canonical_id, token):
    """Re-point all junction rows from source_company → canonical_company.

    Returns (moved, skipped_duplicates).
    """
    rows = fetch_junction_rows(junction_id, company_col, source_id, token)
    moved = 0
    skipped = 0
    for row in rows:
        other_id = row[other_col]
        row_id = row.get("id") or row.get("Id")
        if check_junction_exists(
            junction_id, company_col, other_col, canonical_id, other_id, token
        ):
            # Canonical link already exists → just delete source row
            print(
                f"    junction {junction_id}: ({other_col}={other_id}, {company_col}="
                f"{source_id}) already linked to {canonical_id}, deleting source row"
            )
            if not DRY_RUN:
                delete_junction_row(junction_id, row_id, token)
            skipped += 1
        else:
            print(
                f"    junction {junction_id}: re-point ({other_col}={other_id}) "
                f"from {source_id} → {canonical_id}"
            )
            if not DRY_RUN:
                update_junction_row(
                    junction_id, row_id, {company_col: canonical_id}, token
                )
            moved += 1
    return moved, skipped


def main():
    token = ensure_token()
    mode = "DRY-RUN" if DRY_RUN else "EXECUTE"
    print(f"=== merge-companies.py [{mode}] ===\n")

    print("Discovering junction tables...")
    junctions = discover_junctions(token)
    for title, info in sorted(junctions.items()):
        print(f"  {title} → {info['id']}")
    print()

    # Map of (junction_title_prefix, company_fk_col, other_fk_col)
    junction_specs = [
        # (junction title contains, FK col for Companies, FK col for other side)
        ("Contacts_Companies", "nc_uts0___Companies_id", "nc_uts0___Contacts_id"),
        ("Companies_Roles", "nc_uts0___Companies_id", "nc_uts0___Roles_id"),
        ("Companies_Activities", "nc_uts0___Companies_id", "nc_uts0___Activities_id"),
        # Companies1s handles Past Orgs — title differs
        ("Contacts_Companies1", "nc_uts0___Companies_id", "nc_uts0___Contacts_id"),
        ("Job Postings_Companies", "nc_uts0___Companies_id", "nc_uts0___Job Postings_id"),
    ]

    for merge in MERGES:
        label = merge["label"]
        canonical_id = merge["canonical_id"]
        sources = merge["sources"]
        print(f"─── Merge: {label} (canonical {canonical_id}, sources {sources}) ───")

        # 1. Enrich canonical
        if merge["enrich"]:
            print(f"  Enriching Company {canonical_id} with {list(merge['enrich'].keys())}")
            if not DRY_RUN:
                update_record(COMPANIES_TABLE, canonical_id, merge["enrich"], token)

        # 2. Role title updates
        for role_id, new_title in merge["role_title_updates"].items():
            print(f"  Updating Role {role_id} title → {new_title!r}")
            if not DRY_RUN:
                update_record(ROLES_TABLE, role_id, {"Title": new_title}, token)

        # 3. Re-point junctions
        for source_id in sources:
            print(f"  Re-pointing links from Company {source_id} → {canonical_id}")
            for title_match, company_col, other_col in junction_specs:
                for jtitle, jinfo in junctions.items():
                    if title_match in jtitle:
                        try:
                            moved, skipped = relink_company(
                                jinfo["id"], company_col, other_col,
                                source_id, canonical_id, token,
                            )
                            if moved or skipped:
                                print(
                                    f"    {jtitle}: {moved} re-pointed, "
                                    f"{skipped} dup-skipped"
                                )
                        except RuntimeError as e:
                            print(f"    {jtitle}: ERROR {e}")

        # 4. Delete source Company records
        for source_id in sources:
            print(f"  Deleting Company {source_id}")
            if not DRY_RUN:
                try:
                    delete_record(COMPANIES_TABLE, source_id, token)
                except RuntimeError as e:
                    print(f"    DELETE failed: {e}")
        print()

    print(f"=== {mode} complete ===")
    if DRY_RUN:
        print("\nRe-run with --execute to apply changes.")


if __name__ == "__main__":
    main()
