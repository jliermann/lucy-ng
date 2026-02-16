# Plan 40-01 Summary: Database Regeneration

## Result: COMPLETE

**Duration:** ~8 hours 39 minutes (20:08 - 04:47)
**Tasks:** 1/1

## Task 1: Verify database state and start regeneration

### What was done

1. **Discovered schema mismatch:** Database reported schema version 6 via `schema_meta` table, but actual `hose_stats` table had only v3 columns (6 columns: hose_code, radius, mean, std, count, m2). Detection columns (sp2_count, sp3_count, has_carbon_neighbor, etc.) were missing entirely.

2. **Root cause:** Prior migration set schema version to 6 without actually running ALTER TABLE statements. The `--fresh` flag on first attempt cleared data but didn't fix schema, and the upsert backward-compatibility code silently dropped detection data on v3 schema.

3. **Fix applied:** Reset `schema_meta.schema_version` from 6 to 3, then ran programmatic migrations `migrate_to_v4()` → `migrate_to_v5()` → `migrate_to_v6()` which added all 11 detection columns via ALTER TABLE.

4. **Regeneration:** Ran `lucy database generate-hose-stats --sdf predicted_coconut.sdf --fresh` processing 895,120 molecules in 90 chunks of 10K. Machine kept awake via `caffeinate -d -t 32400`.

### Verification Results

| Metric | Value | Expected |
|--------|-------|----------|
| Total HOSE stats | 7,890,374 | ~7.9M |
| Hybridisation populated | 7,890,374 (100%) | >90% |
| Neighbour populated | 7,827,363 (99.2%) | >90% |
| Compounds processed | 895,099 | 895,120 |
| Compounds failed | 21 | <100 |
| Total shifts processed | 141,801,354 | - |

**Detection CLI verification:**
- `lucy detect hybridisation 128.0`: sp2=1.00 (100% aromatic) — correct
- `lucy detect neighbours 180.0`: oxygen=95.7% mandatory, carbon=97.4% mandatory — correct (carbonyl region)
- Full regression: 755 passed, 7 skipped, 0 failures

### Deviation

Schema version mismatch required manual fix (reset version + re-migrate). First regeneration attempt (without migration) wrote 293K rows with basic stats only and crashed after chunk 1. Orchestrator identified and fixed the issue before restarting regeneration.

## Commits

No code changes — database file is not version-controlled.

## Artifacts

- `data/reference/lucy-ng-derep.db` — v6 schema, 7.89M HOSE stats with full detection columns
