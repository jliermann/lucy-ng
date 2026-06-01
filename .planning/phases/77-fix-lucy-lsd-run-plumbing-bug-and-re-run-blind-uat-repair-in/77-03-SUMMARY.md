---
phase: 77
plan: "03"
subsystem: skill-hygiene
tags:
  - skill-files
  - deprecated-agent
  - lsd-engineer
  - case-orchestrator
  - devils-advocate
  - uat-criteria
dependency_graph:
  requires:
    - "77-01 (FIX-01 code fix — corrects the outlsd plumbing that lsd-engineer now correctly documents)"
    - "77-02 (FIX-02 aromatic-cosy CLI — the CLI reference added here depends on the command existing)"
  provides:
    - "Retired lucy-case-agent.md (cannot be accidentally spawned)"
    - "Corrected lsd-engineer skill (Phase-73 false claim removed, FIX-01 attribution, aromatic-cosy reference, N=3 escalation rule)"
    - "D-77-06 UAT criteria in case.md (Phase 78 handoff)"
    - "COSY within-group check in devils-advocate (G-COSY-EQUIV gate)"
  affects:
    - "Phase 78 blind re-UAT (inherits D-77-06 pass/fail criteria)"
    - "All future CASE runs (agents read corrected skill files)"
tech_stack:
  added: []
  patterns:
    - "Targeted skill-file edits (no full rewrite — per D-77-05)"
    - "YAML frontmatter name neutralization for deprecated agent"
key_files:
  created: []
  modified:
    - "~/.claude/agents/lucy-case-agent.md (frontmatter name neutralized)"
    - "~/.claude/agents/lucy-lsd-engineer.md (3 targeted edits + 2 deviation residual fixes)"
    - "~/.claude/commands/lucy-ng/case.md (D-77-06 UAT criteria step added)"
    - "~/.claude/agents/lucy-devils-advocate.md (G-COSY-EQUIV gate + aromatic-cosy reference)"
decisions:
  - "N=3 as ring-BOND escalation threshold (D-77-01 left this to executor discretion)"
  - "G-COSY-EQUIV added as named check in Bug Checklist (rather than renumbering into G1-G8 — G5-G8 Note says do not renumber existing gates)"
  - "D-77-06 UAT criteria placed as dedicated <step name=uat_criteria> in case.md (not buried in monitor_progress)"
metrics:
  duration: "~25 minutes (interactive session with human-verify checkpoint at Task 3)"
  completed: "2026-06-01T15:54:54Z"
  tasks_completed: 4
  files_modified: 4
  deviation_count: 1
---

# Phase 77 Plan 03: Skill Hygiene — Retire Deprecated Agent + Correct lsd-engineer + Encode D-77-06 UAT Criteria

**One-liner:** Retired deprecated lucy-case-agent (frontmatter neutralized), corrected 5 false Phase-73 "fix works" claims in lsd-engineer (attributing working behavior to Phase 77 FIX-01), added deterministic `lucy detect aromatic-cosy` CLI references and N=3 escalation rule, and encoded the D-77-06 emergent/conditional/fail UAT gate in case.md and devils-advocate.

## What Was Built

### Task 1: lucy-case-agent.md retired

- Changed `name: lucy-case-agent` → `name: DEPRECATED-lucy-case-agent` in frontmatter
- No other changes — historical record and `> DEPRECATED -- DO NOT USE` blockquote preserved
- Verified no active skill or command file references the non-deprecated name

### Task 2: lucy-lsd-engineer.md corrected (3 targeted edits)

**Edit 1 — Phase-73 false claim (lines ~124-130):**
Replaced "Phase 73 fix — `_invoke_outlsd` runs internally after the solver completes" with an accurate correction: Phase 73 unified the helper but did not fix the filter-file deployment gap; Phase 77 FIX-01 corrects both issues.

**Edit 2 — `lucy detect aromatic-cosy` CLI reference (after equiv-pair tagging paragraph):**
Added full CLI syntax, ibuprofen example (`COSY 4 7` + `COSY 5 6`), and a CRITICAL warning that hand-deriving atom indices risks within-group pairs (LSD error 283).

**Edit 3 — D-04 escalation wording (near line 583):**
Updated from "SKEL benzene is an ESCALATION OPTION ONLY for..." to the new rule: ring-BOND forcing allowed only after 3 consecutive non-aromatic iterations, with CASE-PROGRESS logging mandatory; SKEL `c1ccccc1` is forbidden in all cases; undocumented ring-BONDs fail the Phase 78 UAT gate.

### Deviation fix applied before Task 4 (see Deviations section):

Two residual Phase-73 false attributions in lsd-engineer corrected (lines ~581 and ~611).

### Task 4: case.md + lucy-devils-advocate.md updated

**case.md — new `<step name="uat_criteria">` added:**
Encodes D-77-06 in three explicit categories:
- EMERGENT RING = clean pass
- RING-BONDS AS DOCUMENTED ESCALATION = conditional pass (3-iteration rule + CASE-PROGRESS entry)
- SILENT RING-BONDS OR ANY SKEL = fail

Includes quick gate check bash snippet for Phase 78 use.

**lucy-devils-advocate.md — two targeted edits:**
1. "Expected (Normal) Changes" COSY line updated to note `lucy detect aromatic-cosy` guarantees cross-ring pairing.
2. New `G-COSY-EQUIV [COSY Aromatic Equivalence — Within-Group Pair Check]` added in Bug Checklist after Bug 2. This gate is CRITICAL severity and detects the exact Phase-76 failure mode (adjacent `COSY 4 5` instead of cross-ring `COSY 4 7`). Authoritative source for pairs is `lucy detect aromatic-cosy`.

**G5-G8 Phase-75 gates verified intact** — all 4 present and unmodified.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two residual Phase-73 false attributions in lsd-engineer**
- **Found during:** Human review at Task 3 checkpoint
- **Issue:** Task 2 corrected the heading section (lines 124-130) but missed two inline comments further down that still read "(Phase 73 fix)" and "(Phase 73)", falsely implying the solutions.smi production was working before Phase 77. These directly contradicted the corrected text added in Task 2.
- **Fix:** Changed line ~581 from `(Phase 73 fix)` to `(Phase 77 FIX-01 — see Status correction above)` and line ~611 from `(Phase 73)` to `(Phase 77 FIX-01)`.
- **Files modified:** `~/.claude/agents/lucy-lsd-engineer.md`
- **Applied before:** Task 4 (approved at checkpoint as condition of resuming)

## Known Stubs

None. All skill edits reference functional tools (FIX-01 and FIX-02 from Plans 77-01 and 77-02).

## Threat Flags

None. All threat model items from the plan's STRIDE register were addressed:
- T-77-03-01 (Spoofing — accidental agent spawn): mitigated by frontmatter name change
- T-77-03-02 (Tampering — false Phase-73 claim): mitigated — 5 false references corrected (3 from Task 2 + 2 deviation fix)
- T-77-03-03 (Spoofing — compound-specific COSY index guidance): mitigated — CLI tool reference replaces hand-derivation
- T-77-03-04 (Tampering — missing D-77-06 criteria): mitigated — criteria encoded in case.md and DA

## Targeted Audit Findings (D-77-05 scope)

Reviewed all 4 active skill files:

| File | Size | Issues Found | Disposition |
|------|------|-------------|-------------|
| `lucy-lsd-engineer.md` | ~640 lines | 5 Phase-73 false attributions (all corrected), D-04 escalation wording stale | Fixed in this plan |
| `lucy-devils-advocate.md` | ~583 lines | No COSY within-group check for Phase-76 failure mode; G5-G8 intact | Added G-COSY-EQUIV |
| `case.md` | ~593 lines | No D-77-06 UAT criteria for Phase 78 handoff; emergent-ring guidance present (not buried) | Added uat_criteria step |
| `lucy-case-agent.md` | ~1291 lines | Active-looking frontmatter (name not deprecated) | Neutralized |

Full consolidation rewrite remains deferred per D-77-05.

## Self-Check: PASSED

All 12 acceptance criteria verified:

| Check | Result |
|-------|--------|
| 1. `name: DEPRECATED-lucy-case-agent` in case-agent | 1 (PASS) |
| 2. Old bare `name: lucy-case-agent$` gone | 0 (PASS) |
| 3. `aromatic-cosy` in lsd-engineer | 3 (PASS) |
| 4. `3 consecutive non-aromatic` threshold present | 1 (PASS) |
| 5. `SKEL.*forbidden` in lsd-engineer | 1 (PASS) |
| 6. `FIX-01\|Phase 77` in lsd-engineer | 5 (PASS) |
| 7. No remaining `Phase 73 fix` / `Phase 73)` false claims | 0 (PASS) |
| 8. `emergent ring\|EMERGENT RING` in case.md | 3 (PASS) |
| 9. `SKEL.*fail\|silent.*fail` in case.md | 2 (PASS) |
| 10. `aromatic-cosy` in devils-advocate | 3 (PASS) |
| 11. G5/G6/G7/G8 gates intact in devils-advocate | 8 matches (PASS) |
| 12. No active references to non-deprecated agent name | 0 (PASS) |

All 4 skill files exist. 77-03-SUMMARY.md exists.
