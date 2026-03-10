---
phase: 58-operations
plan: 01
subsystem: skills
tags: [status-check, smoke-test, version-compatibility, case-orchestrator, skill-ux]

# Dependency graph
requires:
  - phase: 57-skill-ux
    provides: status.md and case.md skill files with established UX patterns
provides:
  - Version compatibility check with MINIMUM_REQUIRED_VERSION in status.md
  - Smoke test mode (--smoke-test flag) in case.md with 1-iteration validation
affects: [users-of-status-skill, users-of-case-skill, future-operations-plans]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - MINIMUM_REQUIRED_VERSION constant at top of check step for easy updates
    - Semver comparison via split-on-dot integer comparison in agent skill instructions
    - SMOKE_TEST flag pattern for alternative early-exit code path
    - Checkpoint tracking (3-of-3) as pass/fail gate in smoke test
    - Structured SMOKE TEST RESULTS table with per-checkpoint PASS/FAIL status

key-files:
  created: []
  modified:
    - ~/.claude/commands/lucy-ng/status.md
    - ~/.claude/commands/lucy-ng/case.md

key-decisions:
  - "MINIMUM_REQUIRED_VERSION = 0.1.0 defined inline in check_lucy step for easy future updates"
  - "Smoke test defaults to data/Ibuprofen + C13H18O2 as the canonical well-known test dataset"
  - "Smoke test tracks exactly 3 checkpoints: SETUP-COMPLETE, ITERATION-COMPLETE, VALIDATION-PASSED/BLOCKED"
  - "Smoke test exits before ranking — validates pipeline integrity, not CASE correctness"

patterns-established:
  - "Inline version constant: define MINIMUM_REQUIRED_VERSION at top of check step so it is easy to bump"
  - "SMOKE_TEST flag: parallel early-exit path does not alter normal flow, just adds early termination condition"

requirements-completed: [OPER-01, OPER-02]

# Metrics
duration: 2min
completed: 2026-03-10
---

# Phase 58 Plan 01: Operations — Status + Smoke Test Summary

**Version compatibility check in status.md (semver INCOMPATIBLE status) and --smoke-test mode in case.md (1-iteration pass/fail validation of the full CASE team pipeline)**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-10T15:41:03Z
- **Completed:** 2026-03-10T15:43:02Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- status.md check_lucy step now parses `lucy, version X.Y.Z` output and does semver comparison against MINIMUM_REQUIRED_VERSION = 0.1.0
- INCOMPATIBLE status added as third status alongside OK and MISSING, with upgrade instruction and report-level summary message
- case.md parse_arguments now detects `--smoke-test` flag, defaults to Ibuprofen data/formula, prints SMOKE TEST header
- case.md monitor_progress exits after 1 iteration in smoke test mode by tracking 3 checkpoints (SETUP-COMPLETE, ITERATION-COMPLETE, VALIDATION-*)
- New smoke_test_report step generates structured PASS/FAIL table for each of 4 checkpoints (team spawn + 3 message types)
- terminate_team step updated to list smoke_test_report as a valid predecessor

## Task Commits

Note: Skill files at `~/.claude/commands/lucy-ng/` are outside the lucy-ng git repository and cannot be individually committed. Changes are documented in the final metadata commit.

1. **Task 1: Add version compatibility check to status.md** — edit applied to ~/.claude/commands/lucy-ng/status.md
2. **Task 2: Add smoke test mode to case.md** — edits applied to ~/.claude/commands/lucy-ng/case.md

**Plan metadata:** Recorded in final docs commit.

## Files Created/Modified
- `~/.claude/commands/lucy-ng/status.md` — Added MINIMUM_REQUIRED_VERSION, semver comparison, INCOMPATIBLE status and report entry
- `~/.claude/commands/lucy-ng/case.md` — Added --smoke-test parsing, smoke test early exit in monitor_progress, new smoke_test_report step, updated terminate_team predecessor note

## Decisions Made
- MINIMUM_REQUIRED_VERSION = 0.1.0 (current release) defined directly in check_lucy step so future bumps are obvious
- Smoke test defaults to `data/Ibuprofen` + `C13H18O2` — canonical test dataset with known correct structure (ibuprofen)
- Smoke test tracks exactly 3 message-type checkpoints (not iteration count), ensuring all 3 specialist roles participated
- Smoke test does NOT run ranking — validates pipeline plumbing, not CASE accuracy
- 5-minute timeout per checkpoint in smoke test mode as fail-safe

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

Skill files at `~/.claude/commands/lucy-ng/` exist outside the lucy-ng git repository. Per-task commits as specified in the task commit protocol are not possible for these files. Changes are tracked via SUMMARY.md and the final docs commit in the lucy-ng repo.

## Next Phase Readiness
- status.md now warns users of outdated lucy-ng before they attempt workflows
- Smoke test mode provides fast (<5 min) pipeline validation without running CASE to convergence
- Both tools ready for use; no blockers

---
*Phase: 58-operations*
*Completed: 2026-03-10*
