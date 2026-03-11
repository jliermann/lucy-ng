---
phase: 62-agent-skill-updates
plan: "01"
subsystem: agents
tags: [4j-detection, hmbc, agent-skills, lsd, case-workflow]

# Dependency graph
requires:
  - phase: 61-detection-engine
    provides: lucy detect 4j-batch CLI with three-tier risk classification (likely_4j/possible_4j/unlikely_4j/insufficient_data)
provides:
  - Statistical 4J detection integrated into all 4 CASE agent skill files and orchestrator
  - nmr-chemist calls lucy detect 4j-batch for ALL HMBC correlations during setup
  - lsd-engineer handles three risk tiers with deferral cap of 3-4 correlations
  - devils-advocate validates 4J deferral decisions against statistical evidence
  - solution-analyst references statistical 4J scores in aromatic warning
  - case.md orchestrator validates 4J risk scores field in SETUP-COMPLETE messages
affects: [case-workflow, agent-team, 63-full-generation-run, 64-uat]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Three-tier 4J risk handling: likely_4j=defer, possible_4j=HMBC X Y 2 4, unlikely_4j=normal"
    - "Deferral cap: max 3-4 likely_4j correlations; excess demoted to possible_4j treatment"
    - "deferred_4j inventory field changed from string array to object array with risk_level and probability"

key-files:
  created: []
  modified:
    - "~/.claude/agents/lucy-nmr-chemist.md - Section 3 replaced with statistical CLI call"
    - "~/.claude/agents/lucy-lsd-engineer.md - 4J Deferral Rule updated to three-tier, inventory schema updated"
    - "~/.claude/agents/lucy-devils-advocate.md - 4J Risk Score Validation check added"
    - "~/.claude/agents/lucy-solution-analyst.md - Check 6 root cause note and aromatic warning updated"
    - "~/.claude/commands/lucy-ng/case.md - message validation updated to require 4J risk scores field"

key-decisions:
  - "nmr-chemist runs lucy detect 4j-batch on ALL HMBC correlations (not just aromatic) — batch call once during setup"
  - "possible_4j uses HMBC X Y 2 4 extended bond range (not deferred) — only likely_4j is deferred"
  - "Deferral cap of 3-4 correlations prevents combinatorial explosion; excess demoted to possible_4j treatment"
  - "deferred_4j inventory field is now object array [{correlation, risk_level, probability}] not string array"
  - "4J Batch Final uses standard HMBC X Y (not 2 4) because deferred correlations are high-probability 4J"

patterns-established:
  - "Statistical evidence flow: nmr-chemist 4J risk scores -> lsd-engineer three-tier handling -> devils-advocate validation"
  - "SETUP-COMPLETE field renamed from Potential 4J correlations to 4J risk scores with probability and observation count"

requirements-completed: [AGT-01, AGT-02, AGT-03, AGT-04]

# Metrics
duration: 3min
completed: 2026-03-11
---

# Phase 62 Plan 01: Agent Skill Updates Summary

**Statistical 4J detection integrated across all 4 CASE agent skills: nmr-chemist calls `lucy detect 4j-batch`, lsd-engineer applies three-tier risk handling (defer/extend/normal), devils-advocate validates deferral decisions, solution-analyst cites statistical evidence.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-11T09:59:12Z
- **Completed:** 2026-03-11T10:02:44Z
- **Tasks:** 2
- **Files modified:** 5 (all user-level config files outside git repo)

## Accomplishments
- Replaced heuristic shift-range 4J detection (Section 3 of nmr-chemist) with `lucy detect 4j-batch` CLI call on ALL HMBC correlations during setup
- Implemented three-tier risk handling in lsd-engineer: likely_4j deferred (cap 3-4), possible_4j uses `HMBC X Y 2 4` extended bond range, unlikely_4j/insufficient_data treated as normal HMBC
- Added 4J Risk Score Validation check to devils-advocate that verifies deferral justification, cap compliance, and high-risk inclusion against statistical evidence
- Updated solution-analyst Check 6 to reference statistical 4J scores as confirming evidence for aromatic ring failures
- Updated case.md orchestrator message validator to require "4J risk scores" field (replacing "Potential 4J correlations")

## Task Commits

These files are user-level config files at `~/.claude/` (outside git repo). No per-task git commits apply. Changes are tracked in this SUMMARY.

1. **Task 1: Update nmr-chemist and solution-analyst** - surgical markdown edits applied (no git hash)
2. **Task 2: Update lsd-engineer, devils-advocate, and case.md** - surgical markdown edits applied (no git hash)

## Files Created/Modified
- `~/.claude/agents/lucy-nmr-chemist.md` - Section 3 replaced: heuristic "4J HMBC Coupling Detection (Aromatic Systems)" removed; new "Statistical 4J Coupling Detection" section with `lucy detect 4j-batch` CLI call, three-tier interpretation table; [SETUP-COMPLETE] template updated from "Potential 4J correlations:" to "4J risk scores:" with probability/observation format; workflow step 6a updated to call batch CLI
- `~/.claude/agents/lucy-lsd-engineer.md` - 4J Deferral Rule rewritten for three-tier handling; workflow step 2a updated; `deferred_4j` schema changed to object array; example JSON updated with object array; [ITERATION-COMPLETE] 4J status field updated; 4J Batch Final section updated with statistical evidence references
- `~/.claude/agents/lucy-devils-advocate.md` - "4J Risk Score Validation" check added after Aromatic Ring Expectation; [VALIDATION-PASSED] and [VALIDATION-BLOCKED] templates updated with 4J deferral check field
- `~/.claude/agents/lucy-solution-analyst.md` - Check 6 root cause note extended with reference to statistical 4J risk scores from `lucy detect 4j-batch`; [RANKING-COMPLETE] aromatic warning updated to cite 4J risk score confirmation
- `~/.claude/commands/lucy-ng/case.md` - [SETUP-COMPLETE] required field changed from "Potential 4J correlations" to "4J risk scores (required — from `lucy detect 4j-batch`)"

## Decisions Made
- **lucy detect 4j-batch on ALL HMBC (not just aromatic):** The batch CLI runs on every correlation, not just aromatic-to-benzylic. The database covers all atom-type pairs so this is more thorough and avoids the need for aromatic system detection logic.
- **possible_4j uses HMBC X Y 2 4, not deferral:** Medium-risk correlations should be included with extended bond range rather than deferred, to provide constraint information while allowing flexibility.
- **Deferral cap 3-4:** Prevents combinatorial explosion from too many deferred constraints. Excess likely_4j correlations are demoted to possible_4j treatment (HMBC X Y 2 4).
- **4J Batch Final uses standard HMBC X Y:** Deferred correlations are already known to be high-probability 4J; using HMBC X Y 2 4 would validate them as 3-4J which defeats the purpose of the test.
- **deferred_4j as object array:** Object format carries risk_level and probability alongside the correlation string, enabling devils-advocate to validate probability thresholds without re-reading [SETUP-COMPLETE].

## Deviations from Plan

None - plan executed exactly as written. All 10 changes applied as specified in the plan's action blocks.

## Issues Encountered

None. Files were outside the git repo as noted in the plan's important_notes section.

## Next Phase Readiness
- All 4 CASE agent skill files updated with statistical 4J detection integration
- Phase 63 (Full Generation Run) can proceed — agents now use `lucy detect 4j-batch` output from Phase 61's CLI
- Phase 64 (UAT) will exercise the new three-tier handling with real compound data

---
*Phase: 62-agent-skill-updates*
*Completed: 2026-03-11*
