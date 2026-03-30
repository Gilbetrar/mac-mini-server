# Organization Match Report — Issue #21

Generated 2026-03-30. Compares EA Jobs organizations (835 records, 343 unique orgs) against Contacts Companies (353 records).

## Summary

| Category | Count | Action |
|----------|-------|--------|
| Exact matches | 35 | Auto-link to existing Company |
| High confidence (abbreviation diffs) | 12 | Auto-link (all verified correct) |
| True matches in medium band | 4 | Auto-link after Ben confirms |
| Missed acronym matches | 3 | Auto-link after Ben confirms |
| False positive medium matches | 24 | Ignore (different orgs) |
| New orgs (2+ job postings) | 48 | Create new Company records |
| New orgs (1 job posting) | 97 | Create new Company records |
| **Total unique EA orgs** | **343** | |

After merging, estimated Companies table: ~353 existing + ~145 new = **~498 companies**.

---

## Auto-Linkable: Exact Matches (35)

These organizations have identical names in both databases. No review needed.

| EA Jobs Org | Company ID | Jobs |
|-------------|-----------|------|
| 80,000 Hours | 219 | 5 |
| Ambitious Impact | 229 | 1 |
| Animal Ask | 25 | 2 |
| Animal Charity Evaluators | 112 | 1 |
| Anthropic | 338 | 44 |
| Apollo Research | 6 | 11 |
| Aquatic Life Institute | 123 | 3 |
| Astera | 168 | 2 |
| BlueDot Impact | 239 | 4 |
| Blueprint Biosecurity | 130 | 3 |
| Centre for Effective Altruism | 89 | 7 |
| Coefficient Giving | 79 | 5 |
| Constellation | 185 | 11 |
| Epoch AI | 284 | 4 |
| Fish Welfare Initiative | 339 | 4 |
| Forecasting Research Institute | 99 | 9 |
| Founders Pledge | 142 | 1 |
| GiveWell | 218 | 5 |
| Giving What We Can | 271 | 5 |
| Goodfire | 86 | 11 |
| Google DeepMind | 275 | 12 |
| High Impact Athletes | 143 | 1 |
| Longview Philanthropy | 164 | 1 |
| Malaria Consortium | 220 | 1 |
| New Incentives | 146 | 1 |
| One for the World | 327 | 1 |
| OpenAI | 140 | 31 |
| Palisade Research | 230 | 2 |
| Redwood Research | 135 | 1 |
| SaferAI | 349 | 3 |
| Suvita | 45 | 1 |
| The Good Food Institute | 52 | 3 |
| The Humane League | 132 | 1 |
| Wild Animal Initiative | 96 | 1 |
| xAI | 152 | 4 |

## Auto-Linkable: High Confidence (12)

Same org, Contacts name includes abbreviation in parentheses. All verified correct.

| EA Jobs Org | Contacts Company | Company ID | Confidence |
|-------------|-----------------|-----------|------------|
| Against Malaria Foundation | Against Malaria Foundation (AMF) | 60 | 0.90 |
| Alignment Research Center | Alignment Research Center (ARC) | 318 | 0.89 |
| Alliance to Feed the Earth in Disasters | Alliance to Feed the Earth in Disasters (ALLFED) | 166 | 0.90 |
| Center for AI Safety | Center for AI Safety (CAIS) | 249 | 0.85 |
| Center on Long-Term Risk | Centre on Long-term Risk (CLR) | 274 | 0.85 |
| Centre for the Governance of AI | Centre for the Governance of AI (GovAI) | 104 | 0.89 |
| Control AI | ControlAI | 100 | 0.95 |
| Future of Life Institute | Future of Life Institute (FLI) | 122 | 0.89 |
| Innovations for Poverty Action | Innovations for Poverty Action (IPA) | 10 | 0.91 |
| Institute for Progress | Institute for Progress (IFP) | 200 | 0.88 |
| Lead Exposure Elimination Project | Lead Exposure Elimination Project (LEEP) | 102 | 0.90 |
| Machine Intelligence Research Institute | Machine Intelligence Research Institute (MIRI) | 236 | 0.92 |

## Ben to Review: True Matches in Medium Band (4)

These look correct but need confirmation. The algorithm found them with moderate scores.

| EA Jobs Org | Contacts Company | Company ID | Confidence | Notes |
|-------------|-----------------|-----------|------------|-------|
| Gi Effektivt | GiEffektivt.No | 111 | 0.85 | Same org, different name format |
| Good Impressions Media | Good Impressions | 237 | 0.84 | Likely same org |
| Survival and Flourishing | Survival and Flourishing Fund (SFF) | 147 | 0.81 | Same org family |
| UK Government, AI Security Institute | AI Security Institute | 65 | 0.74 | Also matches "UK AI Safety Institute (now AI Security Institute)" (243) |

## Ben to Review: Missed Acronym Matches (3)

The string-matching algorithm missed these because the EA Jobs name is fully expanded while Contacts uses an acronym. Verified by website/context.

| EA Jobs Org | Contacts Company | Company ID | Jobs | Notes |
|-------------|-----------------|-----------|------|-------|
| Model Evaluation and Threat Research | METR | 163 | 5 | metr.org — same org |
| MATS Research | MATS | 14 | 3 | matsprogram.org — same org |
| Evidence Action | Evidence Action (Deworm the World Initiative programme) | 295 | 4 | Same org |

## Ben to Review: Possible Matches Needing Context (3)

| EA Jobs Org | Possible Contacts Match | Notes |
|-------------|------------------------|-------|
| RAND Corporation | Rand (Company ID 311) | Contacts has "Rand" — is this RAND Corporation? Also "RAND CAST" (ID 50) exists separately |
| Animal Equality | (no match) | animalequality.org — distinct from "Animal Ethics" (254) |
| EA Funds | Long-Term Future Fund (39)? | EA Funds runs the LTFF but they're different entities |

## False Positives in Medium Band (24)

These are NOT the same org — the algorithm was fooled by string similarity. No action needed.

Adobe/Doebem, Apart Research/Apollo Research, Aspen Institute/Sentience Institute, Center for Democracy and Technology/CSET, Claryx/Clay, Deep Science Ventures/Effective Ventures, Effectief Geven/Effective Ventures, Egmont Institute/Sentience Institute, Foresight Institute/Forecasting Research Institute, Gates Foundation/SCI Foundation, Harmony Intelligence/Canoe Intelligence, HealthLearn/Healthie, High Impact Medicine/High Impact Athletes, Hudson Institute/Credence Institute, INHR/INSHUR, Institute for Security and Technology/RAND CAST, Malengo/Alpenglow, Mila/Omilia, Mozilla Foundation/SCI Foundation, Open Philanthropy/Longview Philanthropy, Openchip/OpenAI, Poseidon Research/Apollo Research, Secure World Foundation/SCI Foundation, The Royal Society/The Future Society, Valthos/Avantos

## New Organizations — No Match (145)

These EA Jobs organizations don't exist in the Contacts Companies table. New Company records will be created for them during the migration.

### High-activity new orgs (2+ job postings): 48

Top new orgs by job count:
- PopVax (11 jobs)
- MIT FutureTech (9 jobs)
- MIT Lincoln Laboratory (9 jobs)
- RAND Corporation (7 jobs) — check if Contacts "Rand" (ID 311) is this
- Sinergia Animal (7 jobs)
- Amodo Design (6 jobs)
- Faculty (6 jobs)
- Center for AI Risk Management and Alignment (5 jobs)
- LawZero (5 jobs)
- Lawrence Livermore National Laboratory (5 jobs)

### Single-posting new orgs: 97

These will be created as new Company records with minimal metadata.

---

## Enrichment Opportunities

EA Jobs has org metadata (Website, HQ, Cause Areas) that can fill gaps in existing Company records. After matching is confirmed, enrichment will be applied during the migration.

## Next Steps

1. **Ben reviews** the 10 items above (4 medium matches + 3 acronym matches + 3 context-needed)
2. **Agent creates** Job Postings table in Contacts base
3. **Agent imports** EA Jobs records as Job Postings linked to Companies
4. **Agent creates** new Company records for unmatched orgs
5. **Agent renames** Roles → Applications
6. **Agent deletes** standalone EA Jobs base
