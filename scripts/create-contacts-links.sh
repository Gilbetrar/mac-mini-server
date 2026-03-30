#!/bin/bash
# Create link columns between Contacts base tables in NocoDB.
# Run via: ssh mac-mini-remote 'bash -s' < scripts/create-contacts-links.sh
#
# Table IDs:
#   Contacts:   mor9pdbxxz7i6gy
#   Companies:  mk6e9lanspt27rg
#   Activities: m3924zh9ss3wmdf
#   Roles:      mnoqjf6ajrnx7vn

set -e

TOKEN=$(cat ~/services/nocodb/.api-token)
API="http://localhost:8080"

create_link() {
    local parent_table=$1
    local child_table=$2
    local title=$3
    local reverse_title=$4

    echo "Creating: $title ($parent_table -> $child_table)"

    # Create the link column
    RESPONSE=$(curl -s -X POST "$API/api/v2/meta/tables/$parent_table/columns" \
        -H "xc-auth: $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"title\":\"$title\",\"uidt\":\"Links\",\"type\":\"mm\",\"parentId\":\"$parent_table\",\"childId\":\"$child_table\"}")

    # Extract the link column ID from response
    LINK_COL_ID=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
cols = data.get('columns', [])
for c in cols:
    if c.get('title') == '$title' and c.get('uidt') == 'Links':
        print(c['id'])
        break
")
    echo "  Created column: $LINK_COL_ID"

    # Find and rename the reverse column on the child table
    CHILD_COLS=$(curl -s "$API/api/v2/meta/tables/$child_table" \
        -H "xc-auth: $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
cols = data.get('columns', [])
# The newest Links column that isn't named $reverse_title yet
for c in reversed(cols):
    if c.get('uidt') == 'Links' and c.get('title') != '$reverse_title':
        # Check it's the one pointing to our parent table by looking at LTAR
        print(c['id'])
        break
")

    if [ -n "$CHILD_COLS" ]; then
        echo "  Renaming reverse column $CHILD_COLS -> $reverse_title"
        curl -s -X PATCH "$API/api/v2/meta/columns/$CHILD_COLS" \
            -H "xc-auth: $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"title\":\"$reverse_title\"}" > /dev/null
    fi

    echo "  Done"
}

# Rename the already-created reverse column from "Contacts" -> "Current Employees"
echo "Renaming existing reverse column on Companies..."
curl -s -X PATCH "$API/api/v2/meta/columns/cfmbs9obgi1mztv" \
    -H "xc-auth: $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title":"Current Employees"}' > /dev/null
echo "  Done"

# Relationship 2: Contacts.Past Orgs <-> Companies.Past Employees
create_link "mor9pdbxxz7i6gy" "mk6e9lanspt27rg" "Past Orgs" "Past Employees"

# Relationship 3: Contacts.Activities <-> Activities.Contacts
create_link "mor9pdbxxz7i6gy" "m3924zh9ss3wmdf" "Activities" "Contacts"

# Relationship 4: Contacts.Roles <-> Roles.Hiring Manager
create_link "mor9pdbxxz7i6gy" "mnoqjf6ajrnx7vn" "Roles" "Hiring Manager"

# Relationship 5: Companies.Roles <-> Roles.Company
create_link "mk6e9lanspt27rg" "mnoqjf6ajrnx7vn" "Roles" "Company"

# Relationship 6: Companies.Activities <-> Activities.Companies
create_link "mk6e9lanspt27rg" "m3924zh9ss3wmdf" "Activities" "Companies"

# Relationship 7: Activities.Roles <-> Roles.Activities
create_link "m3924zh9ss3wmdf" "mnoqjf6ajrnx7vn" "Roles" "Activities"

echo ""
echo "All 7 link columns created!"
echo ""

# Print summary of all link columns
echo "=== Contacts table link columns ==="
curl -s "$API/api/v2/meta/tables/mor9pdbxxz7i6gy" -H "xc-auth: $TOKEN" | \
    python3 -c "import sys,json; cols=json.load(sys.stdin)['columns']; [print(f'  {c[\"id\"]} | {c[\"title\"]} | {c[\"uidt\"]}') for c in cols if c['uidt'] in ('Links','LinkToAnotherRecord')]"

echo "=== Companies table link columns ==="
curl -s "$API/api/v2/meta/tables/mk6e9lanspt27rg" -H "xc-auth: $TOKEN" | \
    python3 -c "import sys,json; cols=json.load(sys.stdin)['columns']; [print(f'  {c[\"id\"]} | {c[\"title\"]} | {c[\"uidt\"]}') for c in cols if c['uidt'] in ('Links','LinkToAnotherRecord')]"

echo "=== Activities table link columns ==="
curl -s "$API/api/v2/meta/tables/m3924zh9ss3wmdf" -H "xc-auth: $TOKEN" | \
    python3 -c "import sys,json; cols=json.load(sys.stdin)['columns']; [print(f'  {c[\"id\"]} | {c[\"title\"]} | {c[\"uidt\"]}') for c in cols if c['uidt'] in ('Links','LinkToAnotherRecord')]"

echo "=== Roles table link columns ==="
curl -s "$API/api/v2/meta/tables/mnoqjf6ajrnx7vn" -H "xc-auth: $TOKEN" | \
    python3 -c "import sys,json; cols=json.load(sys.stdin)['columns']; [print(f'  {c[\"id\"]} | {c[\"title\"]} | {c[\"uidt\"]}') for c in cols if c['uidt'] in ('Links','LinkToAnotherRecord')]"
