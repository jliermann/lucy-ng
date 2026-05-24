---
phase: "75"
plan: "04"
slug: python-schema-followups
subsystem: cli/fragment
tags: [deff-namespace, filter-index, ring-exclusion, fragment-goodlist, lsd-skill]
dependency_graph:
  requires: ["75-01"]
  provides: ["F-number namespace safety for CASE agent"]
  affects: ["lucy fragment to-lsd", "lsd-engineer.md fragment goodlist section"]
tech_stack:
  added: []
  patterns: ["click option default change", "F-number reservation convention"]
key_files:
  created: []
  modified:
    - src/lucy_ng/cli/fragment.py
    - tests/test_lsd_formatter.py
    - ~/.claude/agents/lucy-lsd-engineer.md
decisions:
  - "Fragment goodlist uses F3+ by default; ring exclusion F1/F2 are reserved namespace"
  - "fragment search multi-result DEFF output left unchanged (uses F1..Fn) — CASE agent always uses to-lsd --top 1, not search"
  - "Added test for F5 in addition to F1/F3 to cover arbitrary filter_index"
metrics:
  duration: "~20 minutes"
  completed: "2026-05-24"
  tasks_completed: 1
  tasks_total: 1
  files_changed: 3
---

# Phase 75 Plan 04: Python Schema Follow-ups Summary

DEFF F-number namespace collision fixed: `lucy fragment to-lsd` now defaults to `--filter-index 3` (F3), keeping F1/F2 reserved exclusively for ring exclusion; 11 fragment-F1 references in lsd-engineer.md updated to F3 with ring-exclusion F1/F2 left intact.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add --filter-index to fragment to-lsd, update tests, update lsd-engineer.md | 129ef03 | fragment.py, test_lsd_formatter.py, lucy-lsd-engineer.md |

## What Was Built

### Python CLI Change (src/lucy_ng/cli/fragment.py)

Added `--filter-index N` click option to `lucy fragment to-lsd` (default 3). The hardcoded `DEFFFormatter.deff_command(1, ...)` and `fexp_command([1])` calls are now parameterized as `deff_command(filter_index, ...)` and `fexp_command([filter_index])`.

Also added a comment to the `fragment search` multi-result DEFF block explaining why that path still uses F1..Fn (CASE agent always uses `to-lsd --top 1`, not `search`; deferred for future multi-fragment support).

CLI matched the plan's assumption exactly — `DEFFFormatter.deff_command` and `fexp_command` already accepted arbitrary integers.

### Test Coverage (tests/test_lsd_formatter.py)

Added `TestToLsdFilterIndex` class with three tests:
- `test_to_lsd_default_filter_index_is_3`: default run → DEFF F3 / FEXP "F3"
- `test_to_lsd_explicit_filter_index_1`: `--filter-index 1` → DEFF F1 / FEXP "F1" (backward compat)
- `test_to_lsd_explicit_filter_index_5`: `--filter-index 5` → DEFF F5 / FEXP "F5" (arbitrary index)

Added `CliRunner` fixture and `json` + `fragment` imports at module level.

### Skill File Edits (~/.claude/agents/lucy-lsd-engineer.md)

11 fragment-F1 references updated to F3 (ring-exclusion F1/F2 left intact throughout):

| Location | What changed |
|----------|-------------|
| CLI example in Fragment Goodlist section | Added `--filter-index 3` to `lucy fragment to-lsd` |
| `deff_command` JSON output field description | "DEFF F1" → "DEFF F3 (F1/F2 reserved for ring exclusion)" |
| LSD file ordering rule | `DEFF F1 "filename.lsd"` → `DEFF F3 "filename.lsd"` |
| Fragment persistence rule | "Carry DEFF F1/FEXP" → "Carry the fragment DEFF F3/FEXP... same as ring-exclusion DEFF F1/F2/FEXP" |
| Zero-solution fallback step 1 (OPERATIONAL BUG FIX) | "Remove DEFF F1 and FEXP lines" → "Remove the fragment DEFF Fn and FEXP lines (Fn = F3 by default — check deff_command in inventory; do NOT remove ring-exclusion DEFF F1/F2 lines)" |
| Manual checklist item 10 | "DEFF F1/FEXP present" → "DEFF F3/FEXP present (F3 = fragment goodlist; F1/F2 = ring exclusion — distinct namespaces)" |
| Inventory JSON example deff_command | `"DEFF F1 \"fragment_abc123def456.lsd\""` → F3 |
| Inventory JSON example fexp_command | `"FEXP \"F1\""` → `"FEXP \"F3\""` |
| Raw LSD example after inventory block | `DEFF F1` + `FEXP "F1"` → F3 |
| Initialization Procedure step 5a | "DEFF F1/FEXP lines go after inventory block" → "DEFF F3/FEXP lines go after inventory block (F3 = fragment goodlist, reserved above ring-exclusion F1/F2)" |
| Update Procedure step (carry forward) | "carry forward DEFF F1/FEXP lines" → "carry forward DEFF F3/FEXP lines (check deff_command in inventory for actual Fn)" |
| Workflow step 6 (LSD file build order) | "then DEFF F1/FEXP (if fragment applied)" → "then DEFF F3/FEXP (if fragment applied)" |

Ring-exclusion references confirmed intact: lines 151-153 (standard block), 156 (F-number reservation note), 159 (epoxide exception), 218 (checklist item 8), 475 (initialization procedure critical note).

## Schema Check

`schemas/constraint_inventory_v2.json` already has `additionalProperties: true` at line 20. No schema change needed — confirmed.

## Verification Results

```
PASS: default F3: DEFF F3 "fragment_ab1de819ede9.lsd"
PASS: explicit F1: DEFF F1 "fragment_ab1de819ede9.lsd"
PASS: schema accepts new fields
```

pytest test_lsd_formatter.py: 31 passed
pytest full suite: 1007 passed, 7 skipped, 1 xfailed

## Deviations from Plan

### Auto-adaptation: Extra test added

The plan specified 2 new tests (default F3, explicit F1). A third test (`test_to_lsd_explicit_filter_index_5`) was added to verify arbitrary filter indices work, providing better coverage of the parameterization. Minor additive deviation.

### Adaptation: Post-75-01 lsd-engineer.md reality

Per the critical heads-up, the plan's line numbers were written against pre-75-01 text. Several old_strings were adapted to the post-75-01 content. No functional intent was lost — all 11 fragment-F1 references found and updated. The ring-exclusion-vs-fragment distinction in the file was already established by 75-01 (F-number reservation note at line 156); this plan completes it by updating all usage examples.

None - no bugs found, no architectural changes needed.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes at trust boundaries.

## Self-Check: PASSED

- src/lucy_ng/cli/fragment.py: FOUND
- tests/test_lsd_formatter.py: FOUND
- Python commit 129ef03: FOUND
- grep "Remove the fragment DEFF Fn" ~/.claude/agents/lucy-lsd-engineer.md: FOUND (line 198)
- grep "same as the ring-exclusion DEFF F1/F2" ~/.claude/agents/lucy-lsd-engineer.md: FOUND (line 195)
- grep "carry forward DEFF F1/FEXP": 0 matches (good — no stale fragment-F1 carry-forward instruction)
