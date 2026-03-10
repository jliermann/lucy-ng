---
phase: 57-skill-ux
plan: 02
subsystem: ui
tags: [skill-ux, error-recovery, dry-run, predict, dereplicate, sanitise, claude-commands]

requires: []
provides:
  - HOSE code miss error recovery guidance in predict.md with 3 actionable suggestions
  - Zero-match error recovery guidance in dereplicate.md with 4 troubleshooting steps
  - Dry-run confirmation gate in sanitise.md before any file modifications
affects: [predict, dereplicate, sanitise]

tech-stack:
  added: []
  patterns:
    - "Error recovery sections in skill present_results steps for edge case outcomes"
    - "Dry-run gate pattern: scan READ-ONLY first, present manifest, require 'proceed' confirmation before writes"

key-files:
  created: []
  modified:
    - ~/.claude/commands/lucy-ng/predict.md (HOSE miss guidance added to present_results step)
    - ~/.claude/commands/lucy-ng/dereplicate.md (0-match guidance added to present_results step)
    - ~/.claude/commands/lucy-ng/sanitise.md (dry_run_scan and present_dry_run_report steps added)

key-decisions:
  - "Dry-run step is READ-ONLY — explicitly states 'Do NOT use Write tool or rm commands' to prevent accidental modification"
  - "sanitise.md requires exact string 'proceed' (not just any confirmation) to prevent ambiguous responses from triggering modifications"
  - "HOSE miss guidance positioned after error cases in present_results — it's a partial-success case, not a failure"

patterns-established:
  - "Error recovery pattern: Report what failed, explain root cause (database coverage), suggest 3-4 concrete alternatives"
  - "Dry-run gate pattern: classify → scan (read-only) → present manifest → await 'proceed' → execute"

requirements-completed: [SKUX-03, SKUX-04, SKUX-05]

duration: 3min
completed: 2026-03-10
---

# Phase 57 Plan 02: Skill UX — Error Recovery and Dry-Run Summary

**Error recovery guidance added to predict and dereplicate skills for edge cases (HOSE misses, 0 database matches), and a read-only dry-run confirmation gate added to sanitise before any file modifications.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-10T15:00:37Z
- **Completed:** 2026-03-10T15:03:46Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- predict.md: Added dedicated section in `present_results` for HOSE code miss case — reports affected atoms, explains database coverage limitation, gives 3 actionable fixes (canonical SMILES, remove stereochemistry, check unusual functional groups)
- dereplicate.md: Added dedicated section in `present_results` for 0-match case — reports no compounds found, gives 4 troubleshooting steps including formula spelling, related formulas, database coverage note, and CASE referral
- sanitise.md: Inserted `dry_run_scan` and `present_dry_run_report` steps between discover and delete phases — agent reads all files and builds a manifest, then presents a report and waits for explicit "proceed" before any file is modified or deleted

## Task Commits

Note: Skill files are in `~/.claude/commands/lucy-ng/` (outside the lucy-ng git repository). Changes are applied directly to those files; no per-task git commits exist for them. Only planning metadata is committed to the repo.

1. **Task 1: Add HOSE miss guidance to predict.md and 0-match guidance to dereplicate.md** - external file edit (outside repo)
2. **Task 2: Add dry-run step to sanitise.md** - external file edit (outside repo)

**Plan metadata:** (see final docs commit)

## Files Created/Modified

- `~/.claude/commands/lucy-ng/predict.md` - New section: "If some atoms have no predictions (HOSE code miss)" with 3 suggestions and confidence note
- `~/.claude/commands/lucy-ng/dereplicate.md` - New section: "If 0 matches returned" with 4 troubleshooting steps and CASE referral
- `~/.claude/commands/lucy-ng/sanitise.md` - Two new steps added: `dry_run_scan` (READ-ONLY scan) and `present_dry_run_report` (manifest + "proceed"/"cancel" gate); `delete_structure_and_audit_files` and `scan_and_redact` updated with "runs after user confirmation" notes

## Decisions Made

- Dry-run requires the exact string "proceed" to continue — any other response triggers cancellation with "No files were modified" confirmation. This prevents accidental triggering from vague confirmations.
- HOSE miss guidance is placed after the error cases block (not alongside them) because it is a partial-success scenario — the CLI succeeded but coverage was incomplete.
- 0-match guidance references CASE as the fallback option because it is the natural next step when the compound is not in the database.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

The skill files reside in `~/.claude/commands/lucy-ng/` which is outside the lucy-ng git repository. Per-task commits were therefore not possible; the skill file edits are applied directly, and only the planning metadata is committed to the repo. This is the same pattern established in Phase 57 Plan 01.

## Next Phase Readiness

- All three skills now handle their primary edge cases with actionable guidance
- sanitise is protected against accidental file modification via dry-run gate
- Phase 57 skill UX improvements complete (plans 01 and 02)

---
*Phase: 57-skill-ux*
*Completed: 2026-03-10*
