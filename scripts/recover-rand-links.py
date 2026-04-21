#!/usr/bin/env python3
"""Recovery: re-create junction rows linking RAND's contacts/role/activities to Company 431.

The original merge-companies.py PATCH failed (junction PK was None), and the
subsequent DELETE of Companies 50 and 311 cascade-deleted the junction rows.
This script re-inserts fresh junction rows pointing to Company 431 (canonical
RAND Corporation).

Data comes from the pre-merge dry-run output.
"""
import json
import os
import sys
import urllib.request
import urllib.error
import subprocess

NOCODB_URL = "http://localhost:8080"
CONTACTS_BASE = "p4b83cic6kiud9b"

CANONICAL = 431

LINKS = [
    # (junction_table_id, company_fk_col, other_fk_col, other_id)
    ("mm375v0y4lmezkm", "nc_uts0___Companies_id", "nc_uts0___Contacts_id", 186),
    ("mm375v0y4lmezkm", "nc_uts0___Companies_id", "nc_uts0___Contacts_id", 236),
    ("mm375v0y4lmezkm", "nc_uts0___Companies_id", "nc_uts0___Contacts_id", 329),
    ("mm375v0y4lmezkm", "nc_uts0___Companies_id", "nc_uts0___Contacts_id", 287),
    ("m4pmrpbinopg4wd", "nc_uts0___Companies_id", "nc_uts0___Contacts_id", 14),
    ("m1y3ddrl9qv6t3m", "nc_uts0___Companies_id", "nc_uts0___Roles_id", 14),
    ("mav5v1ftufxhx4j", "nc_uts0___Companies_id", "nc_uts0___Activities_id", 85),
    ("mav5v1ftufxhx4j", "nc_uts0___Companies_id", "nc_uts0___Activities_id", 99),
    ("mav5v1ftufxhx4j", "nc_uts0___Companies_id", "nc_uts0___Activities_id", 4),
    ("mav5v1ftufxhx4j", "nc_uts0___Companies_id", "nc_uts0___Activities_id", 86),
    ("mav5v1ftufxhx4j", "nc_uts0___Companies_id", "nc_uts0___Activities_id", 12),
    ("mav5v1ftufxhx4j", "nc_uts0___Companies_id", "nc_uts0___Activities_id", 76),
    ("mav5v1ftufxhx4j", "nc_uts0___Companies_id", "nc_uts0___Activities_id", 92),
]


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
    token = json.loads(urllib.request.urlopen(req).read())["token"]
    with open(os.path.expanduser("~/services/nocodb/.api-token"), "w") as f:
        f.write(token)
    return token


def post(path, token, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{NOCODB_URL}{path}",
        data=body,
        method="POST",
        headers={"xc-auth": token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        err = e.read().decode() if e.fp else ""
        raise RuntimeError(f"HTTP {e.code}: {err[:500]}")


def ensure_token():
    token = get_token()
    try:
        req = urllib.request.Request(
            f"{NOCODB_URL}/api/v1/db/meta/projects/{CONTACTS_BASE}/tables",
            headers={"xc-auth": token},
        )
        urllib.request.urlopen(req).read()
        return token
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("Refreshing token...")
            return refresh_token()
        raise


def main():
    token = ensure_token()
    print(f"Re-inserting {len(LINKS)} junction rows linking to Company {CANONICAL}\n")

    ok = 0
    fail = 0
    for junction_id, co_col, other_col, other_id in LINKS:
        row = {co_col: CANONICAL, other_col: other_id}
        try:
            result = post(
                f"/api/v1/db/data/noco/{CONTACTS_BASE}/{junction_id}",
                token, row,
            )
            print(f"  ✓ {junction_id} ({other_col}={other_id}) → {CANONICAL}")
            ok += 1
        except RuntimeError as e:
            print(f"  ✗ {junction_id} ({other_col}={other_id}): {e}")
            fail += 1

    print(f"\nDone. {ok} inserted, {fail} failed.")


if __name__ == "__main__":
    main()
