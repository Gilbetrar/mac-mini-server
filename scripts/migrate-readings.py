#!/usr/bin/env python3
"""Migrate Ben Readings & Notes from Airtable JSON exports to NocoDB.

Reads Airtable data from MCP-exported JSON files, transforms to NocoDB format,
and pushes via NocoDB API on Mac Mini.
"""

import json
import subprocess
import sys
import tempfile
import os

# Airtable data files (exported by MCP)
DATA_DIR = "/Users/benjaminbateman/.claude/projects/-Users-benjaminbateman-AI-Projects-mac-mini-server/7a0723c6-bc69-43a2-8d50-e616890c6239/tool-results"
DATA_FILES = [
    f"{DATA_DIR}/mcp-claude_ai_Airtable-list_records_for_table-1774120272722.txt",
    f"{DATA_DIR}/mcp-claude_ai_Airtable-list_records_for_table-1774120289623.txt",
    f"{DATA_DIR}/mcp-claude_ai_Airtable-list_records_for_table-1774120302391.txt",
    f"{DATA_DIR}/mcp-claude_ai_Airtable-list_records_for_table-1774120312352.txt",
]

# NocoDB config
BASE_ID = "pz0snc66hf3yi5f"
TABLE_ID = "meut1xg8f13dy9w"
BATCH_SIZE = 100

# Airtable field ID → NocoDB column title
FIELD_MAP = {
    "fld73g46Kil4zqIm4": "Title",
    "fldHnL3EMCN5yGyUi": "Type",
    "fldSE13FcQT8yZ18N": "Reading Status",
    "fldpIUfGw4IRrcGxt": "Priority",
    "fldr6HoXioOji4yQw": "Author",
    "fldVf5twaqlUMZXlO": "Description",
    "fldFUctQZaICFJ7Pm": "Link",
    "fld63tVb6SCScphx8": "Cards?",
    "fldcg45aFQOrkvUhj": "Date acquired",
    "fldvLKxmbTATBBbaT": "Obsidian Filepath",
    "fldQgMVEfxhe4QViQ": "Subtitle",
    "fldegQNMCYQT99F8J": "Has title card?",
    "fldvxZSpvIWc4EJI9": "Source",
    "fldmjGKOAkvs8snpS": "Rating",
}

# Fields with SingleSelect values (Airtable returns {id, name, color})
SELECT_FIELDS = {"Type", "Reading Status", "Priority", "Cards?", "Has title card?", "Source"}

# Fields to skip (auto-managed or too complex)
SKIP_AIRTABLE_FIELDS = {"fldcPPA5oERAhIi7N", "fld3ECMmgTGSH5AYJ"}


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
        elif noco_title == "Rating":
            value = int(value) if value else None
        if value is not None:
            noco[noco_title] = value
    return noco


def load_all_records():
    """Load and transform all records from data files."""
    all_records = []
    for filepath in DATA_FILES:
        with open(filepath) as f:
            data = json.load(f)
            all_records.extend(data["records"])
    return [transform_record(r) for r in all_records]


def push_batch(batch):
    """Push a batch of records to NocoDB via SSH to Mac Mini."""
    # Write batch to local temp file, scp to Mac Mini, then POST
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(batch, f)
        tmp_path = f.name

    try:
        # SCP to Mac Mini
        subprocess.run(
            ["scp", "-q", tmp_path, "mac-mini:/tmp/noco-batch.json"],
            check=True, capture_output=True
        )

        # POST via curl
        result = subprocess.run(
            [
                "ssh", "mac-mini",
                'TOKEN=$(cat ~/services/nocodb/.api-token); '
                f'curl -s -X POST "localhost:8080/api/v1/db/data/bulk/noco/{BASE_ID}/{TABLE_ID}" '
                '-H "xc-auth: $TOKEN" -H "Content-Type: application/json" '
                '-d @/tmp/noco-batch.json'
            ],
            capture_output=True, text=True
        )
        return result.stdout
    finally:
        os.unlink(tmp_path)


def get_record_count():
    """Get current record count from NocoDB."""
    result = subprocess.run(
        [
            "ssh", "mac-mini",
            'TOKEN=$(cat ~/services/nocodb/.api-token); '
            f'curl -s "localhost:8080/api/v1/db/data/noco/{BASE_ID}/{TABLE_ID}?limit=1" '
            '-H "xc-auth: $TOKEN"'
        ],
        capture_output=True, text=True
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
    print(f"  Sample: {sample.get('Title', '?')[:60]} by {sample.get('Author', '?')}")

    # Check current state
    current = get_record_count()
    if current > 0:
        print(f"  WARNING: Table already has {current} records. Aborting to avoid duplicates.")
        sys.exit(1)

    # Push in batches
    total_batches = (len(records) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        response = push_batch(batch)

        # NocoDB bulk returns [] on success
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
