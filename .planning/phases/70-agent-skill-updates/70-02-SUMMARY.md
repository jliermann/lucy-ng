---
phase: 70-agent-skill-updates
plan: "02"
subsystem: agent-skills
tags: [devils-advocate, G4, permutation-cap, pylsd-mode, validation-gate]
dependency_graph:
  requires: [67-01, 68-04]
  provides: [AGT-04]
  affects: [lucy-devils-advocate.md]
tech_stack:
  added: []
  patterns: [G-gate-subcheck, bash-python3-json-extraction, VALIDATION-PASSED-template]
key_files:
  created: []
  modified:
    - /Users/steinbeck/.claude/agents/lucy-devils-advocate.md
decisions:
  - "G4 reuses $RESULT from §5A — no second CLI call (D-18 design)"
  - "K≤3 cap mirrors PyLSDOrchestrator.run() ValueError — pre-run fail-fast (D-18)"
  - "nmr-chemist named as resolution owner in BLOCK message (D-18b / Pitfall 7)"
  - "G4 + summary line update atomic — Pitfall 3 guard applied"
metrics:
  duration: "~8 minutes"
  completed: "2026-05-19T20:34:00Z"
  tasks_completed: 1
  files_changed: 1
---

# Phase 70 Plan 02: devils-advocate G4 Permutation Cap Summary

**One-liner:** G4 permutation-cap gate inserted in §5B Check 4 as fourth sub-check, blocking when K>3 before PyLSDOrchestrator raises ValueError; VALIDATION-PASSED template extended with `pyLSD mode:` field.

## Tasks Completed

| Task | Name | Files Changed |
|------|------|---------------|
| 1 | Insert G4 sub-check, update summary line, extend VALIDATION-PASSED template | `/Users/steinbeck/.claude/agents/lucy-devils-advocate.md` |

## What Was Built

**G4: Permutation Count Cap** was inserted as the fourth sub-check in §5B Check 4 of `lucy-devils-advocate.md`, between the G3 block and the "All gates" summary sentence.

The G4 block:
- Counts `deferred_4j` entries from `$RESULT` (already set in §5A from `lucy lsd validate-inventory --format json`) using a Python one-liner
- Issues a CRITICAL BLOCK when K > 3, naming: K value, 2^K=8 permutation count, K≤3 cap, `PyLSDOrchestrator.run()` ValueError, and `nmr-chemist` as resolution owner
- Passes silently when K ≤ 3 (including when `pylsd_mode=false`, since the outer check skips Check 4 entirely)
- Reuses `$RESULT` — no second CLI call needed (confirmed against §5A §225-253)

The "All three gates G1/G2/G3" summary sentence was updated atomically to "All four gates G1/G2/G3/G4 are CRITICAL severity and blocking" (Pitfall 3 guard).

The [VALIDATION-PASSED] template received a new `pyLSD mode:` field after `Aromatic ring check:`, documenting the three states: N/A (pylsd_mode=false), PASS (K=N, N≤3), BLOCKED (K=N>3).

## Deviations from Plan

None — plan executed exactly as written. All three edits applied as specified in PLAN.md action block.

## Verification Results

All acceptance criteria passed:

| Check | Result |
|-------|--------|
| `grep "G4"` | PASS |
| `grep "Permutation Count Cap"` | PASS |
| `grep "K > 3"` | PASS |
| `grep "deferred_4j"` | PASS |
| `grep "PyLSDOrchestrator"` | PASS |
| `grep "nmr-chemist"` | PASS |
| `grep "All four gates G1/G2/G3/G4"` | PASS |
| `grep "pyLSD mode:"` | PASS |
| `grep -c "All three gates G1/G2/G3 are CRITICAL"` → 0 | PASS |
| `pytest tests/ -q` → exit code 0 | PASS (no Python changes; suite confirms no regression) |

## Known Stubs

None.

## Threat Flags

None. No new network endpoints, auth paths, or schema changes. Skill file edit only.

## Self-Check: PASSED

- `/Users/steinbeck/.claude/agents/lucy-devils-advocate.md` — modified in-place (confirmed via grep verification above)
- `.planning/phases/70-agent-skill-updates/70-02-SUMMARY.md` — this file
- No commit hash for the skill file (it lives outside the git worktree at `~/.claude/agents/`; the GSD workflow commits plan artifacts inside the worktree)
