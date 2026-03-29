#!/usr/bin/env python3
"""Migrate Contacts base from Airtable to NocoDB.

Handles 4 tables: Contacts, Companies, Activities, Roles.
Step 1: Creates tables and imports non-link data.
Step 2 (future): Creates link columns and links records.

Reads Airtable data from MCP-exported JSON files, transforms to NocoDB format,
and pushes via NocoDB API on Mac Mini.
"""

import json
import subprocess
import sys
import tempfile
import os

# === DATA FILES ===
DATA_DIR = "/Users/benjaminbateman/.claude/projects/-Users-benjaminbateman-AI-Projects-mac-mini-server/59427e44-dd4b-4ebe-a88c-6c002334d579/tool-results"
CONTACTS_FILE = f"{DATA_DIR}/mcp-claude_ai_Airtable-list_records_for_table-1774809643169.txt"
COMPANIES_FILE = f"{DATA_DIR}/mcp-claude_ai_Airtable-list_records_for_table-1774809644366.txt"
ACTIVITIES_FILE = f"{DATA_DIR}/mcp-claude_ai_Airtable-list_records_for_table-1774809646054.txt"
ROLES_FILE = f"{DATA_DIR}/roles-data.json"  # Saved separately (small table)

# === NOCODB CONFIG ===
BASE_ID = "p4b83cic6kiud9b"
BATCH_SIZE = 100

# === TABLE DEFINITIONS ===
# Each table: (name, fields_to_import, select_fields, skip_fields)
# fields_to_import: {airtable_field_id: (nocodb_title, nocodb_uidt)}
# select_fields: set of nocodb_titles that are SingleSelect/MultiSelect
# skip_fields: set of airtable_field_ids to skip entirely

TABLES = {
    "Contacts": {
        "file": CONTACTS_FILE,
        "fields": {
            "fldWf1s7npSz69BZ7": ("Full name", "SingleLineText"),
            "fldQTcuCZBlHO3Jp7": ("Notes", "LongText"),
            "fldQvcAJG0gjLXmc7": ("Tags", "MultiSelect"),
            "fldl7zIuXLqlpY7JJ": ("Expertise", "MultiSelect"),
            "fld7b43lRd8AIB0w9": ("Company", "SingleLineText"),
            "fld9fUTqZtfPWsCjo": ("Current Title", "SingleLineText"),
            "fldneQHq0mioTInmv": ("Work email", "Email"),
            "fld1Ao1WLhdDe7OE9": ("Personal Email", "Email"),
            "fldW16q2OS1Aj1kEU": ("LinkedIn", "URL"),
            "fldBciPm1ldObDxGJ": ("Phone", "PhoneNumber"),
            "fldx1wl2sBEbBUu0R": ("Location", "SingleLineText"),
        },
        "select_fields": {"Tags", "Expertise"},
        "multiselect_fields": {"Tags", "Expertise"},
        # Link fields to preserve IDs for later linking
        "link_fields": {
            "fldfqmXnR6w83b4Eh": "Past Orgs",       # → Companies
            "fldxId9y5SDAIjTXd": "Current Org",      # → Companies
            "fldl2QJp7RNAFfgn5": "Activities",       # → Activities
            "fldi7qB7VNmySecJs": "Roles",            # → Roles
        },
    },
    "Companies": {
        "file": COMPANIES_FILE,
        "fields": {
            "fldPiEAX5JBGq2bXb": ("Name", "SingleLineText"),
            "fldOgVs1MVRV03Xxi": ("Website", "URL"),
            "fldYErG8luV7tWBrY": ("Notes", "LongText"),
            "fldtfo3YxpQ6P4lzI": ("Org Type", "MultiSelect"),
            "fldKSssto5oNMDeK9": ("Career Interest", "SingleSelect"),
            "fldxlTpebg48CgjOl": ("Career Priority", "SingleSelect"),
            "fldxwbaSEsrdQiWNe": ("Career Track", "SingleSelect"),
            "fld1dirgJIMoN4bpd": ("Job Hunt Next Step", "SingleSelect"),
            "fldrgIegrGnpSInGz": ("Next Step Notes", "LongText"),
            "fldFDnaCQYjODhXMf": ("Size", "SingleSelect"),
            "fld9LrSequ8gUmdT0": ("Description", "LongText"),
            "fldEQiv4schdTSWLU": ("Jobs Page", "URL"),
            "fldK52j3HW6YDvH8t": ("Last checked jobs page", "Date"),
            "fldRzNWlLsIxkV09f": ("Location", "SingleLineText"),
            "fldBdqg6xAzbdfdIr": ("Career change", "SingleSelect"),
            "fldeZ7xIgwd3HbAZa": ("Remote policy", "SingleSelect"),
        },
        "select_fields": {"Org Type", "Career Interest", "Career Priority", "Career Track",
                          "Job Hunt Next Step", "Size", "Career change", "Remote policy"},
        "multiselect_fields": {"Org Type"},
        "link_fields": {
            "fldQAcfz2nvaUyE5M": "Current Employees",  # → Contacts
            "fldsOxMQXlL7Mo993": "Past Employees",      # → Contacts
            "fldrdW5hwXIS14uIL": "Roles",               # → Roles
            "flduf9qTMs6ejjnO6": "Activities",          # → Activities
        },
    },
    "Activities": {
        "file": ACTIVITIES_FILE,
        "fields": {
            "fld1JvVDBHiNCE3Bi": ("Notes", "LongText"),
            "flduvdeNXcQYQOjPG": ("Date", "Date"),
            "fldxtqP5KxqXe62nq": ("Tags", "MultiSelect"),
            "fldqRXjuA4DkPEHeo": ("Activity type", "SingleSelect"),
            "fldH7AMYGRszGXjyP": ("Followups complete", "Checkbox"),
        },
        "select_fields": {"Tags", "Activity type"},
        "multiselect_fields": {"Tags"},
        # Activity Name is a formula — we'll create a regular text field with the computed value
        "formula_as_text": {
            "fldyN8c2Ie8v4XNzs": ("Activity Name", "SingleLineText"),
        },
        "link_fields": {
            "fldOVOGpLQbVWbNBe": "Contacts",    # → Contacts
            "fldMrof2e8lISdLAg": "Companies",    # → Companies
            "fldKvAzRxSWG2pWXU": "Roles",        # → Roles
        },
    },
    "Roles": {
        "file": ROLES_FILE,
        "fields": {
            "fldTU8zZbZcl0cXJe": ("Title", "SingleLineText"),
            "fld4pEpXLTeANlFBg": ("Application Stage", "SingleSelect"),
            "fldNXmua1xbV0IPNi": ("JD status", "SingleSelect"),
            "flddkN4MxgFplHuLc": ("Location", "SingleSelect"),
            "fldHY7PxIWQACd2Bc": ("Comp (low)", "Currency"),
            "fldf6KTLpXpuMmBlK": ("Comp (high)", "Currency"),
            "fldR1KsFyGojd3Goa": ("JD", "URL"),
            "fld7AAt7TVeHfTknk": ("Notes", "LongText"),
            "fldvlkLL7TxEbP3hy": ("Career Track", "SingleSelect"),
            "fldp5RP9U7tQdfuaT": ("Current Status", "LongText"),
            "fldz2zRZ01FCyMkcL": ("Career Move", "SingleSelect"),
            "fldOBptmlOhkT3hp3": ("Last Contact", "Date"),
            "fldNsAiCBYT7xLFuW": ("Action needed", "SingleSelect"),
        },
        "select_fields": {"Application Stage", "JD status", "Location", "Career Track",
                          "Career Move", "Action needed"},
        "multiselect_fields": set(),
        # Title at Company is a formula — store as text
        "formula_as_text": {
            "fld689O3usHLeeYsk": ("Title at Company", "SingleLineText"),
        },
        "link_fields": {
            "fldO3LPWazIiaphfo": "Company",          # → Companies
            "fldsKavrbZ9O7TN6m": "Activities",        # → Activities
            "fldHCxU0qa5R44mpv": "Hiring Manager",    # → Contacts
        },
    },
}


def log(msg):
    """Print with immediate flush."""
    print(msg, flush=True)


def ssh_cmd(cmd):
    """Run a command on Mac Mini via SSH and return stdout."""
    result = subprocess.run(
        ["ssh", "mac-mini-remote", cmd],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        log(f"  SSH error (rc={result.returncode}): {result.stderr[:200]}")
    return result.stdout


def get_token():
    """Get fresh NocoDB auth token."""
    return ssh_cmd("cat ~/services/nocodb/.api-token").strip()


def scan_select_options(records, table_config):
    """Pre-scan all records to collect unique select/multiselect option values."""
    options = {}  # noco_title -> set of option names

    for record in records:
        fields = record.get("cellValuesByFieldId", {})
        for at_id, (noco_title, noco_uidt) in table_config["fields"].items():
            if noco_title not in table_config.get("select_fields", set()):
                continue
            value = fields.get(at_id)
            if value is None:
                continue

            if noco_title not in options:
                options[noco_title] = set()

            if noco_title in table_config.get("multiselect_fields", set()):
                # MultiSelect: list of {id, name, color}
                if isinstance(value, list):
                    for v in value:
                        if isinstance(v, dict) and "name" in v:
                            options[noco_title].add(v["name"])
            else:
                # SingleSelect: {id, name, color}
                if isinstance(value, dict) and "name" in value:
                    options[noco_title].add(value["name"])

    return {k: sorted(v) for k, v in options.items()}


def create_table(table_name, table_config, select_options):
    """Create a NocoDB table with columns. Returns table ID."""
    columns = [{"title": "Title", "uidt": "SingleLineText"}]  # NocoDB requires a default

    # Regular fields
    for at_id, (noco_title, noco_uidt) in table_config["fields"].items():
        col = {"title": noco_title, "uidt": noco_uidt}
        if noco_uidt == "Currency":
            col["meta"] = {"currency_locale": "en-US", "currency_code": "USD"}
        if noco_title in select_options:
            # Pre-define select options using colOptions (handles commas in names)
            col["colOptions"] = {
                "options": [{"title": opt} for opt in select_options[noco_title]]
            }
        columns.append(col)

    # Formula-as-text fields
    for at_id, (noco_title, noco_uidt) in table_config.get("formula_as_text", {}).items():
        columns.append({"title": noco_title, "uidt": noco_uidt})

    payload = {"title": table_name, "columns": columns}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        tmp_path = f.name

    try:
        subprocess.run(["scp", "-q", tmp_path, "mac-mini-remote:/tmp/noco-create-table.json"],
                       check=True, capture_output=True)
        result = ssh_cmd(
            f'TOKEN=$(cat ~/services/nocodb/.api-token); '
            f'curl -s -X POST "localhost:8080/api/v2/meta/bases/{BASE_ID}/tables" '
            f'-H "xc-auth: $TOKEN" -H "Content-Type: application/json" '
            f'-d @/tmp/noco-create-table.json'
        )
        data = json.loads(result)
        if "id" in data:
            return data["id"]
        else:
            log(f"  ERROR creating table {table_name}: {data}")
            sys.exit(1)
    finally:
        os.unlink(tmp_path)


def transform_record(record, table_config):
    """Transform one Airtable record to NocoDB format."""
    noco = {}
    fields = record.get("cellValuesByFieldId", {})

    # Regular fields
    for at_id, (noco_title, noco_uidt) in table_config["fields"].items():
        value = fields.get(at_id)
        if value is None:
            continue

        if noco_title in table_config.get("multiselect_fields", set()):
            # MultiSelect: Airtable returns [{id, name, color}, ...]
            if isinstance(value, list):
                value = ",".join(v.get("name", str(v)) if isinstance(v, dict) else str(v) for v in value)
        elif noco_title in table_config.get("select_fields", set()):
            # SingleSelect: Airtable returns {id, name, color}
            if isinstance(value, dict):
                value = value.get("name", str(value))
        elif noco_uidt == "Checkbox":
            value = bool(value)
        elif noco_uidt == "Currency":
            value = float(value) if value else None

        if value is not None:
            noco[noco_title] = value

    # Formula-as-text fields (store computed value as plain text)
    for at_id, (noco_title, _) in table_config.get("formula_as_text", {}).items():
        value = fields.get(at_id)
        if value is not None:
            noco[noco_title] = str(value)

    return noco


def extract_link_data(record, table_config):
    """Extract link field data from a record for later linking."""
    links = {}
    fields = record.get("cellValuesByFieldId", {})
    for at_id, link_name in table_config.get("link_fields", {}).items():
        value = fields.get(at_id)
        if value and isinstance(value, list):
            links[link_name] = [v["id"] for v in value if isinstance(v, dict) and "id" in v]
    return links


def push_batch(batch, table_id):
    """Push a batch of records to NocoDB via SSH."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(batch, f)
        tmp_path = f.name

    try:
        subprocess.run(["scp", "-q", tmp_path, "mac-mini-remote:/tmp/noco-batch.json"],
                       check=True, capture_output=True)
        result = ssh_cmd(
            f'TOKEN=$(cat ~/services/nocodb/.api-token); '
            f'curl -s -X POST "localhost:8080/api/v1/db/data/bulk/noco/{BASE_ID}/{table_id}" '
            f'-H "xc-auth: $TOKEN" -H "Content-Type: application/json" '
            f'-d @/tmp/noco-batch.json'
        )
        return result
    finally:
        os.unlink(tmp_path)


def get_record_count(table_id):
    """Get current record count from NocoDB."""
    result = ssh_cmd(
        f'TOKEN=$(cat ~/services/nocodb/.api-token); '
        f'curl -s "localhost:8080/api/v1/db/data/noco/{BASE_ID}/{table_id}?limit=1" '
        f'-H "xc-auth: $TOKEN"'
    )
    try:
        data = json.loads(result)
        return data.get("pageInfo", {}).get("totalRows", 0)
    except (json.JSONDecodeError, KeyError):
        return -1


def migrate_table(table_name, table_config):
    """Create table, transform data, and insert records."""
    log(f"\n{'='*60}")
    log(f"Migrating: {table_name}")
    log(f"{'='*60}")

    # Load data
    filepath = table_config["file"]
    with open(filepath) as f:
        data = json.load(f)

    airtable_records = data["records"]
    expected_count = data["metadata"]["totalRecordCount"]
    log(f"  Loaded {len(airtable_records)} records (expected {expected_count})")

    # Pre-scan select options
    select_options = scan_select_options(airtable_records, table_config)
    for title, opts in select_options.items():
        log(f"  Select options for '{title}': {len(opts)} values")

    # Create table
    log(f"  Creating NocoDB table...")
    table_id = create_table(table_name, table_config, select_options)
    log(f"  Table created: {table_id}")

    # Transform records
    noco_records = []
    id_mapping = {}  # airtable_id -> index (for later linking)
    link_data = {}   # airtable_id -> {link_name: [target_airtable_ids]}

    for i, record in enumerate(airtable_records):
        at_id = record["id"]
        noco_rec = transform_record(record, table_config)
        noco_records.append(noco_rec)
        id_mapping[at_id] = i
        links = extract_link_data(record, table_config)
        if links:
            link_data[at_id] = links

    log(f"  Transformed {len(noco_records)} records")

    # Push in batches
    total_batches = (len(noco_records) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(noco_records), BATCH_SIZE):
        batch = noco_records[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        try:
            response = push_batch(batch, table_id)
        except Exception as e:
            log(f"  Batch {batch_num}/{total_batches}: PUSH FAILED - {e}")
            sys.exit(1)

        if not response or not response.strip():
            log(f"  Batch {batch_num}/{total_batches}: EMPTY RESPONSE")
            sys.exit(1)

        try:
            result = json.loads(response)
            if isinstance(result, list):
                log(f"  Batch {batch_num}/{total_batches}: OK ({len(batch)} records)")
            elif isinstance(result, dict) and "msg" in result:
                log(f"  Batch {batch_num}/{total_batches}: ERROR - {result}")
                sys.exit(1)
            else:
                log(f"  Batch {batch_num}/{total_batches}: UNEXPECTED - {str(result)[:200]}")
                sys.exit(1)
        except json.JSONDecodeError:
            log(f"  Batch {batch_num}/{total_batches}: BAD JSON - {response[:200]}")
            sys.exit(1)

    # Verify
    final_count = get_record_count(table_id)
    log(f"  Final count: {final_count} (expected {expected_count})")

    if final_count == expected_count:
        log(f"  SUCCESS!")
    else:
        log(f"  WARNING: Count mismatch!")

    return {
        "table_id": table_id,
        "id_mapping": id_mapping,
        "link_data": link_data,
        "record_count": final_count,
    }


def main():
    log("=" * 60)
    log("Contacts Base Migration: Airtable → NocoDB")
    log("=" * 60)

    # Verify token works
    token = get_token()
    if not token:
        print("ERROR: No NocoDB token. Run token refresh first.")
        sys.exit(1)

    test = ssh_cmd(
        f'TOKEN=$(cat ~/services/nocodb/.api-token); '
        f'curl -s "localhost:8080/api/v2/meta/bases/{BASE_ID}/tables" '
        f'-H "xc-auth: $TOKEN"'
    )
    try:
        existing = json.loads(test)
        if "list" in existing and len(existing["list"]) > 0:
            print(f"WARNING: Base already has {len(existing['list'])} tables. Aborting to avoid duplicates.")
            for t in existing["list"]:
                print(f"  - {t['title']} ({t['id']})")
            sys.exit(1)
    except json.JSONDecodeError:
        log(f"ERROR: Could not query NocoDB: {test[:200]}")
        sys.exit(1)

    # Migrate all tables
    results = {}
    for table_name in ["Contacts", "Companies", "Activities", "Roles"]:
        config = TABLES[table_name]
        results[table_name] = migrate_table(table_name, config)

    # Save migration metadata (for linking step)
    metadata = {
        table_name: {
            "table_id": r["table_id"],
            "id_mapping": r["id_mapping"],
            "link_data": r["link_data"],
            "record_count": r["record_count"],
        }
        for table_name, r in results.items()
    }

    meta_path = os.path.join(os.path.dirname(__file__), "contacts-migration-metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nMetadata saved to: {meta_path}")

    # Summary
    print(f"\n{'='*60}")
    print("MIGRATION SUMMARY")
    print(f"{'='*60}")
    for table_name, r in results.items():
        print(f"  {table_name}: {r['record_count']} records → {r['table_id']}")
        if r["link_data"]:
            link_count = sum(len(v) for links in r["link_data"].values() for v in links.values())
            print(f"    {link_count} link references saved for future linking")

    print("\nStep 1 complete! Link columns can be created in a follow-up step.")


if __name__ == "__main__":
    main()
