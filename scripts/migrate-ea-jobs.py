#!/usr/bin/env python3
"""Migrate EA Jobs Database from Airtable JSON export to NocoDB.

Reads Airtable data from MCP-exported JSON file, transforms to NocoDB format,
and pushes via NocoDB API on Mac Mini.
"""

import json
import subprocess
import sys
import tempfile
import os

# Airtable data file (exported by MCP)
DATA_FILE = "/Users/benjaminbateman/.claude/projects/-Users-benjaminbateman-AI-Projects-mac-mini-server/e8044b5b-de57-4924-a879-f8e95d24ca20/tool-results/mcp-claude_ai_Airtable-list_records_for_table-1774892969977.txt"

# NocoDB config
BASE_ID = "pxo2rnpo3ud4ulk"
TABLE_ID = "mim7su9us6cxvju"
BATCH_SIZE = 100

# Airtable field ID → NocoDB column title
FIELD_MAP = {
    "fldMwNvAkS2EDPoZ1": "git_id",
    "fldcf8K1W7D8zTIXv": "Title",
    "fldEA8LHnjA4ImrdW": "Organization",
    "fldY4pJkgXlj1FPnN": "Source",
    "fldUpbOFZvrA65Qdd": "Source URL",
    "fldXOUM47mldtidmG": "Status",
    "fld8N69msGkyEkTef": "Location Type",
    "fld4qc5Syphvvq4IL": "Cities",
    "fldhbb6JsTzB5YC87": "Salary Min",
    "fldqDGeItvqgmHKCj": "Salary Max",
    "fld7ga2sZWmkdNLIv": "Salary Currency",
    "fldgs1BvB95HB29sf": "Salary Period",
    "fldhIjUQL1MysIXLW": "Posted Date",
    "fldDPHBFBsC4QMPmE": "Deadline",
    "fldVughQplRfflztI": "Date Added",
    "fldwwgvTdiEVOucTz": "Tags",
    "fldEAW9SP6L7FFG1Y": "Confidence",
    "fldW1UrwAw0U2LtdQ": "Org Website",
    "fldIsXywlI532Nqwj": "Org HQ",
    "fldr5URryhqKqUN5y": "Org Cause Areas",
    "fldlHRHg4kAHs6F3U": "Notes",
    "fldP1NC2Y5UOnbhuQ": "Job Description",
}

# Fields with SingleSelect values (Airtable returns {id, name, color})
SELECT_FIELDS = {"Source", "Status", "Location Type", "Salary Currency", "Salary Period"}

# Fields with MultiSelect values (Airtable returns [{id, name, color}, ...])
MULTI_SELECT_FIELDS = {"Tags"}

# Numeric fields
NUMBER_FIELDS = {"Salary Min", "Salary Max", "Confidence"}


def transform_record(airtable_record):
    """Transform one Airtable record to NocoDB format."""
    noco = {}
    fields = airtable_record.get("cellValuesByFieldId", {})
    for at_id, noco_title in FIELD_MAP.items():
        value = fields.get(at_id)
        if value is None:
            continue
        if noco_title in SELECT_FIELDS:
            value = value.get("name") if isinstance(value, dict) else value
        elif noco_title in MULTI_SELECT_FIELDS:
            if isinstance(value, list):
                value = ",".join(
                    v.get("name") if isinstance(v, dict) else v for v in value
                )
            elif isinstance(value, dict):
                value = value.get("name", "")
        elif noco_title in NUMBER_FIELDS:
            if isinstance(value, (int, float)):
                value = value
            else:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    continue
        if value is not None:
            noco[noco_title] = value
    return noco


def load_all_records():
    """Load and transform all records from data file."""
    with open(DATA_FILE) as f:
        data = json.load(f)
    return [transform_record(r) for r in data["records"]]


def push_batch(batch):
    """Push a batch of records to NocoDB via SSH to Mac Mini."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(batch, f)
        tmp_path = f.name

    try:
        subprocess.run(
            ["scp", "-q", tmp_path, "mac-mini:/tmp/noco-batch.json"],
            check=True,
            capture_output=True,
        )

        result = subprocess.run(
            [
                "ssh",
                "mac-mini",
                'TOKEN=$(cat ~/services/nocodb/.api-token); '
                f'curl -s -X POST "localhost:8080/api/v1/db/data/bulk/noco/{BASE_ID}/{TABLE_ID}" '
                '-H "xc-auth: $TOKEN" -H "Content-Type: application/json" '
                "-d @/tmp/noco-batch.json",
            ],
            capture_output=True,
            text=True,
        )
        return result.stdout
    finally:
        os.unlink(tmp_path)


def get_record_count():
    """Get current record count from NocoDB."""
    result = subprocess.run(
        [
            "ssh",
            "mac-mini",
            'TOKEN=$(cat ~/services/nocodb/.api-token); '
            f'curl -s "localhost:8080/api/v1/db/data/noco/{BASE_ID}/{TABLE_ID}?limit=1" '
            '-H "xc-auth: $TOKEN"',
        ],
        capture_output=True,
        text=True,
    )
    try:
        data = json.loads(result.stdout)
        return data.get("pageInfo", {}).get("totalRows", 0)
    except (json.JSONDecodeError, KeyError):
        return -1


def main():
    print("Loading and transforming Airtable records...")
    records = load_all_records()
    print(f"  {len(records)} records ready")

    # Show sample
    sample = records[0]
    print(f"  Sample: {sample.get('Title', '?')[:60]} @ {sample.get('Organization', '?')}")

    # Check current state
    current = get_record_count()
    if current > 0:
        print(f"  WARNING: Table already has {current} records. Aborting to avoid duplicates.")
        sys.exit(1)

    # Push in batches
    total_batches = (len(records) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        response = push_batch(batch)

        try:
            result = json.loads(response)
            if isinstance(result, list):
                print(f"  Batch {batch_num}/{total_batches}: OK ({len(batch)} records)")
            elif isinstance(result, dict) and "error" in result:
                print(f"  Batch {batch_num}/{total_batches}: ERROR - {result}")
                sys.exit(1)
        except json.JSONDecodeError:
            print(f"  Batch {batch_num}/{total_batches}: unexpected: {response[:200]}")
            sys.exit(1)

    # Verify
    final_count = get_record_count()
    print(f"\nDone! NocoDB now has {final_count} records (expected {len(records)})")

    if final_count == len(records):
        print("SUCCESS: Record counts match!")
    else:
        print(f"WARNING: Count mismatch! Expected {len(records)}, got {final_count}")


if __name__ == "__main__":
    main()
