---
phase: 70-agent-skill-updates
plan: 01
subsystem: agent-skills
tags: [lsd-engineer, pylsd, constraint-inventory, routing-block, iteration-complete]

# Dependency graph
requires:
  - phase: 69-cli-command-and-regression-suite
    provides: lucy pylsd run CLI with --format json output shape
  - phase: 68-constraint-inventory-v2-schema
    provides: validate-inventory CLI returning inventory.pylsd_mode boolean
  - phase: 67-pylsdorchestrator-and-solutionmerger
    provides: PyLSDOrchestrator, SolutionMerger, run_report.json schema
provides:
  - lsd-engineer routing block reading pylsd_mode from constraint inventory
  - conditional lucy pylsd run vs lucy lsd run decision logic in agent skill
  - pyLSD vocabulary subsection documenting SHIX/SHIH/; FORM/HMBC X Y 2 4 syntax
  - ITERATION-COMPLETE template extended with per-permutation table and aggregated block
affects:
  - 70-02 (devils-advocate G4 plan)
  - 71-uat (live CASE test will exercise the routing block)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Solver-mode routing: lsd-engineer reads its own inventory via validate-inventory before every LSD run and selects CLI command based on pylsd_mode boolean (D-17)"
    - "ABSENT inventory silent fallback: .get('inventory',{}).get('pylsd_mode', False) Python expression falls through to lucy lsd run without warning for pre-Phase-68 files (D-19)"

key-files:
  created: []
  modified:
    - /Users/steinbeck/.claude/agents/lucy-lsd-engineer.md

key-decisions:
  - "D-17 encapsulation: routing (lucy pylsd run vs lucy lsd run) lives in lsd-engineer, not case.md — the agent that writes the inventory owns the solver-mode decision"
  - "D-19 ABSENT fallback: .get('inventory',{}).get('pylsd_mode', False) implements silent fallback to single-run mode for files without v2 inventory block"
  - "D-20 ITERATION-COMPLETE blocks conditional on pylsd_mode: per-permutation table + aggregated merged_count/Top-3-SMILES appended after existing 4J status field"
  - "AGT-01: §1 pyLSD vocabulary added as new subsection after ELIM, documents SHIX/SHIH/; FORM/HMBC X Y 2 4 syntax for debugging LSDInputGenerator-generated permutation files"

patterns-established:
  - "Skill-section pyLSD vocabulary: new ### pyLSD Commands (pylsd_mode only) subsection pattern for lsd-engineer §1"
  - "Routing block pattern: bash conditional using validate-inventory --format json + python3 JSON extraction"

requirements-completed:
  - AGT-01
  - AGT-02
  - AGT-03

# Metrics
duration: 15min
completed: 2026-05-19
---

# Phase 70 Plan 01: lsd-engineer pyLSD Routing and Vocabulary Summary

**lsd-engineer now reads pylsd_mode from its own constraint inventory at run-time and conditionally invokes `lucy pylsd run` (multi-run) or `lucy lsd run` (single-run), completing the agent-layer bridge to the Phase 66-69 Python infrastructure**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-05-19T00:00:00Z
- **Completed:** 2026-05-19
- **Tasks:** 2
- **Files modified:** 1 (lucy-lsd-engineer.md, outside repo)

## Accomplishments

- Inserted `### pyLSD Commands (pylsd_mode only)` subsection in §1 after ELIM block, documenting `; FORM` comment convention (error 102 note), `SHIX`/`SHIH` syntax, and `HMBC X Y 2 4` / `HMBC X Y 2 4 ; ELIM` extended-range syntax (AGT-01)
- Replaced both unconditional `lucy lsd run` occurrences: §3 documentation string (line 284) updated to prose pointer; workflow step 11 (line 497) replaced with full conditional routing block that reads `pylsd_mode` from the constraint inventory via `lucy lsd validate-inventory --format json` (AGT-02, D-17)
- Extended ITERATION-COMPLETE template with two conditional pylsd_mode blocks after the existing `4J status:` field: per-permutation table (permutation_id/defer_set/solution_count/top_rank_quality) and aggregated block (merged_count + Top-3 SMILES with data extraction commands) (D-20)
- All 988 pytest tests passed — no regressions

## Task Commits

Note: `~/.claude/agents/lucy-lsd-engineer.md` is outside the git repository. The file was edited in-place. SUMMARY.md is the only git-committed artifact for this plan.

1. **Task 1: Insert pyLSD vocabulary subsection in §1** — in-place edit (no git artifact)
2. **Task 2: Replace unconditional lsd run with routing block + ITERATION-COMPLETE extension** — in-place edit (no git artifact)

## Files Created/Modified

- `/Users/steinbeck/.claude/agents/lucy-lsd-engineer.md` — Added §1 pyLSD vocabulary subsection; replaced §3 documentation string and workflow step 11 with conditional routing block; extended ITERATION-COMPLETE template with pylsd_mode blocks (~50 lines added, 2 lines replaced)

## Decisions Made

- D-17 encapsulation confirmed: routing lives entirely in lsd-engineer, case.md is and remains CLI-agnostic
- D-19 ABSENT fallback: `.get('inventory',{}).get('pylsd_mode', False)` in routing block implements silent fallback to single-run mode for files without v2 inventory (no warning emitted)
- `--working-dir` flag omitted from `lucy pylsd run` call; default `pylsd_run/` subdirectory under LSD file's parent directory is sufficient per Phase 69 D-14 Discretion
- Per-permutation data extraction documented as commands (python3 one-liners + wc -l) rather than inlined scripts — sufficient for agent use

## Deviations from Plan

None — plan executed exactly as written. Both tasks completed with all positive acceptance criteria matching and negative checks confirming removal of old unconditional forms. The single remaining `cd analysis/iteration_NN && lucy lsd run compound.lsd` at workflow step 11 is the intentional `else` branch of the new routing block (D-17 / D-19), not a remnant of the old unconditional invocation.

## Issues Encountered

None.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes. This plan modified only a markdown skill file outside the repository. No new trust boundaries introduced.

## Known Stubs

None — all new content is instructional prose and bash command templates. No data-rendering stubs.

## Self-Check

**Files:**
- `/Users/steinbeck/.claude/agents/lucy-lsd-engineer.md` exists: YES (edited in-place)

**Verification grep results (all passed):**
- `grep "pyLSD Commands (pylsd_mode only)"` — 1 match (line 86)
- `grep "SHIX|SHIH"` — 2 matches (lines 94, 95)
- `grep "bare FORM rejected|error 102"` — 1 match (line 92)
- `grep "HMBC X Y 2 4"` — 4 matches
- `grep "PYLSD_MODE|lucy pylsd run"` — 6 matches
- `grep "pylsd_output.json|merged_count|permutation_id"` — 7 matches
- `grep "4J status:"` — 2 matches (field preserved + conditional block reference)
- `grep "solver-mode routing block"` — 1 match (§3 prose pointer)
- `grep ".get.*pylsd_mode.*False"` — 2 matches (D-19 fallback documented)
- Old unconditional forms: 0 occurrences of `Run LSD: \`cd analysis` (step-11 old form gone)
- case.md unchanged: `grep -c "lucy lsd run|lucy pylsd run" case.md` = 0
- pytest: 988 passed, 7 skipped, 1 xfailed — exit 0

## Self-Check: PASSED

## Next Phase Readiness

- Plan 70-02 (devils-advocate G4 permutation cap check) can proceed independently
- Phase 71 (UAT with live compound) can now exercise the routing block end-to-end
- No blockers

---
*Phase: 70-agent-skill-updates*
*Completed: 2026-05-19*
