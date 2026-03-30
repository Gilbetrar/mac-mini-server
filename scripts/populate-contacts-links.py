#!/usr/bin/env python3
"""Populate link columns in NocoDB Contacts base using metadata from migration.

Reads the contacts-migration-metadata.json to map Airtable record IDs to NocoDB
row IDs, then bulk inserts into junction tables via SSH to Mac Mini.

Usage: python3 scripts/populate-contacts-links.py
"""

import json
import subprocess
import sys

METADATA_FILE = "scripts/contacts-migration-metadata.json"
BATCH_SIZE = 100  # NocoDB bulk insert limit

# Junction table configs: (metadata_table, link_field, mm_table_id, parent_fk_col, child_fk_col, child_table)
# parent = the table where we read link_data from, child = the linked-to table
RELATIONSHIPS = [
    # 1. Contacts.Current Org -> Companies
    ("Contacts", "Current Org", "mm375v0y4lmezkm",
     "nc_uts0___Contacts_id", "nc_uts0___Companies_id", "Companies"),
    # 2. Contacts.Past Orgs -> Companies
    ("Contacts", "Past Orgs", "m4pmrpbinopg4wd",
     "nc_uts0___Contacts_id", "nc_uts0___Companies_id", "Companies"),
    # 3. Contacts.Activities -> Activities
    ("Contacts", "Activities", "mkgbecdf159afxi",
     "nc_uts0___Contacts_id", "nc_uts0___Activities_id", "Activities"),
    # 4. Contacts.Roles -> Roles
    ("Contacts", "Roles", "mzpp6x3uupsfaf2",
     "nc_uts0___Contacts_id", "nc_uts0___Roles_id", "Roles"),
    # 5. Companies.Roles -> Roles
    ("Companies", "Roles", "m1y3ddrl9qv6t3m",
     "nc_uts0___Companies_id", "nc_uts0___Roles_id", "Roles"),
    # 6. Companies.Activities -> Activities
    ("Companies", "Activities", "mav5v1ftufxhx4j",
     "nc_uts0___Companies_id", "nc_uts0___Activities_id", "Activities"),
    # 7. Activities.Roles -> Roles
    ("Activities", "Roles", "m5vncjwux9ht8kz",
     "nc_uts0___Activities_id", "nc_uts0___Roles_id", "Roles"),
]

BASE_ID = "p4b83cic6kiud9b"


def load_metadata():
    with open(METADATA_FILE) as f:
        return json.load(f)


def build_junction_records(meta, table_name, link_field, parent_fk, child_fk, child_table):
    """Build list of junction table records from metadata link_data."""
    table = meta[table_name]
    id_mapping = table["id_mapping"]  # airtable_id -> 0-based index
    child_mapping = meta[child_table]["id_mapping"]
    link_data = table["link_data"]

    records = []
    skipped = 0
    for airtable_id, links in link_data.items():
        if link_field not in links:
            continue
        parent_idx = id_mapping.get(airtable_id)
        if parent_idx is None:
            skipped += 1
            continue
        parent_noco_id = parent_idx + 1  # NocoDB IDs are 1-based

        for child_airtable_id in links[link_field]:
            child_idx = child_mapping.get(child_airtable_id)
            if child_idx is None:
                skipped += 1
                continue
            child_noco_id = child_idx + 1
            records.append({parent_fk: parent_noco_id, child_fk: child_noco_id})

    return records, skipped


def bulk_insert_via_ssh(mm_table_id, records):
    """Bulk insert records into junction table via SSH to Mac Mini."""
    total = len(records)
    inserted = 0

    for i in range(0, total, BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        payload = json.dumps(batch)

        cmd = (
            f'TOKEN=$(cat ~/services/nocodb/.api-token) && '
            f'curl -s -X POST '
            f'"http://localhost:8080/api/v1/db/data/bulk/noco/{BASE_ID}/{mm_table_id}" '
            f'-H "xc-auth: $TOKEN" '
            f'-H "Content-Type: application/json" '
            f"-d '{payload}'"
        )

        result = subprocess.run(
            ["ssh", "mac-mini-remote", cmd],
            capture_output=True, text=True, timeout=60
        )

        if result.returncode != 0:
            print(f"  ERROR: SSH failed: {result.stderr}", file=sys.stderr)
            return inserted

        try:
            response = json.loads(result.stdout)
            if isinstance(response, list):
                inserted += len(response)
            elif "error" in response or "msg" in response:
                print(f"  ERROR: {response}", file=sys.stderr)
                return inserted
        except json.JSONDecodeError:
            print(f"  ERROR: Bad response: {result.stdout[:200]}", file=sys.stderr)
            return inserted

    return inserted


def main():
    print("Loading metadata...")
    meta = load_metadata()

    total_links = 0
    total_skipped = 0

    for table_name, link_field, mm_table_id, parent_fk, child_fk, child_table in RELATIONSHIPS:
        print(f"\n{table_name}.{link_field} -> {child_table}")
        records, skipped = build_junction_records(
            meta, table_name, link_field, parent_fk, child_fk, child_table
        )
        print(f"  Records to insert: {len(records)}, skipped: {skipped}")

        if not records:
            print("  Nothing to insert")
            continue

        inserted = bulk_insert_via_ssh(mm_table_id, records)
        print(f"  Inserted: {inserted}/{len(records)}")
        total_links += inserted
        total_skipped += skipped

    print(f"\n=== Done! Total links created: {total_links}, skipped: {total_skipped} ===")


if __name__ == "__main__":
    main()
