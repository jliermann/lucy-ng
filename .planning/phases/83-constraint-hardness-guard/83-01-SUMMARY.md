---
phase: 83-constraint-hardness-guard
plan: "01"
subsystem: case-agents
tags: [fix-10, constraint-hardness, skill-update, devils-advocate, lsd-engineer, nmr-chemist]
dependency_graph:
  requires: []
  provides: [FIX-10-skill-rules]
  affects: [.claude/agents/lucy-nmr-chemist.md, .claude/agents/lucy-lsd-engineer.md, .claude/agents/lucy-devils-advocate.md]
tech_stack:
  added: []
  patterns: [compound-agnostic-skill-rules, G-PROP-EVIDENCE-gate]
key_files:
  created: []
  modified:
    - .claude/agents/lucy-nmr-chemist.md
    - .claude/agents/lucy-lsd-engineer.md
    - .claude/agents/lucy-devils-advocate.md
decisions:
  - "Full-distribution advisory reading enforced: detect-neighbours output is a statistical prior only, never the sole basis for hard PROP/BOND"
  - "G-PROP-EVIDENCE gate is CRITICAL severity (blocks solver run) — an incorrect hard heteroatom PROP is solution-excluding and ranking cannot recover from it"
  - "Carbonyl exception (convergent multi-source: Cq + 160-220 ppm + C=O context) is the ONLY permitted use of detection to contribute to a hard heteroatom BOND"
  - "145-160 ppm aromatic C explicitly flagged as ambiguous (ring-O vs benzylic/EDG substituent)"
  - "All three agent files remain compound-agnostic — zero CASE9-specific values embedded"
metrics:
  duration: "4 minutes"
  completed: "2026-06-10T16:34:08Z"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 3
---

# Phase 83 Plan 01: Constraint Hardness Guard (FIX-10) Summary

**One-liner:** Three coordinated skill-file edits enforce full-distribution advisory reading of `detect neighbours` output and install the G-PROP-EVIDENCE gate to block hard heteroatom PROP/BOND constraints lacking direct or convergent corroborating evidence.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | nmr-chemist — full-distribution advisory rule + Pitfall 6 FIX-10 | fedb5cd | .claude/agents/lucy-nmr-chemist.md |
| 2 | lsd-engineer — convergent-evidence rule + carbonyl exception | 2388783 | .claude/agents/lucy-lsd-engineer.md |
| 3 | devils-advocate — G-PROP-EVIDENCE gate | d7b844b | .claude/agents/lucy-devils-advocate.md |

## What Was Built

### Task 1 — nmr-chemist

Two targeted edits:

**EDIT A (Pitfall 6):** Replaced the old "express what you KNOW" single-paragraph Pitfall 6 with a comprehensive FIX-10 block that:
- Names `detect neighbours` output as a statistical prior / advisory signal
- Requires reading the FULL distribution (dominant element, constraint_type per element)
- Adds the 145-160 ppm aromatic C ambiguity warning (ring-O vs benzylic/EDG substituent)
- Prohibits renormalization of detect-neighbours frequencies
- Specifies the carbonyl exception (convergent multi-source: Cq + 160-220 ppm + C=O context)
- Restates "let ranking decide" for uncertain heteroatom placements

**EDIT B (Section 5 Neighbours interpretation):** Replaced the old "Mandatory (>95%) -> PROP constraint" shortcut with an 8-step full-distribution advisory protocol. The old rule was the defect mechanism; the new rule makes a statistical prior advisory-only at every step.

### Task 2 — lsd-engineer

Two targeted edits:

**EDIT A (Bond and Property Constraints):** Added FIX-10 PROHIBITION block naming the G-PROP-EVIDENCE gate. Specifies (i) direct connectivity evidence and (ii) convergent multi-source corroboration as the only two permitted bases for hard heteroatom constraints. Lists four forbidden patterns including renormalization, carbon-dominant shifts, and the 145-160 ppm aromatic ambiguity range.

**EDIT B (Manual Checklist item 6):** Replaced the old "BOND for C=O only; LIST/ELEM/PROP for flexible connectivity" with the convergent-evidence rule and explicit reference to the G-PROP-EVIDENCE gate.

### Task 3 — devils-advocate

Three targeted edits:

**EDIT A (G-PROP-EVIDENCE gate definition):** Inserted after G7 in Section 5 Check 5. Full 4-step check procedure including bash greps. Three sub-checks (a) typical constraint_type, (b) carbon-dominant neighbour, (c) renormalized probability — each independently CRITICAL. CRITICAL severity with rationale explaining the failure mode.

**EDIT B (Gate summary table):** Added G-PROP-EVIDENCE row after G7 row.

**EDIT C (Workflow step 8a):** Added G-PROP-EVIDENCE gate check as step 8a after the existing bug checklist step.

## Verification Results

All acceptance criteria passed after two minor case-sensitivity corrections (STATISTICAL PRIOR -> statistical prior to satisfy lowercase grep; Renormalizing -> renormalizing):

| Check | Expected | Actual | Pass |
|-------|----------|--------|------|
| `statistical prior` in nmr-chemist | >=2 | 2 | PASS |
| `dominant` in nmr-chemist | >=2 | 4 | PASS |
| `FIX-10` in nmr-chemist | >=1 | 1 | PASS |
| `145-160 ppm` in nmr-chemist | >=1 | 1 | PASS |
| `renormali` in nmr-chemist | >=1 | 2 | PASS |
| `G-PROP-EVIDENCE` in lsd-engineer | >=2 | 3 | PASS |
| `FIX-10` in lsd-engineer | >=2 | 3 | PASS |
| `convergent` in lsd-engineer | >=2 | 2 | PASS |
| `dominant` in lsd-engineer | >=1 | 2 | PASS |
| `renormali` in lsd-engineer | >=1 | 1 | PASS |
| `G-PROP-EVIDENCE` in devils-advocate | >=4 | 7 | PASS |
| `| G-PROP-EVIDENCE |` table row | >=1 | 1 | PASS |
| `FIX-10` in devils-advocate | >=2 | 2 | PASS |
| `dominant` in devils-advocate | >=2 | 4 | PASS |
| `renormali` in devils-advocate | >=1 | 4 | PASS |
| Compound-agnostic guard (all 3 files) | 0 | 0 | PASS |
| Existing G-ELIM-1 intact | >=1 | 1 | PASS |
| Existing G7 intact | >=1 | 4 | PASS |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Case-sensitivity mismatch in grep acceptance criteria**
- **Found during:** Task 1 verification
- **Issue:** Plan prescribed "STATISTICAL PRIOR" (uppercase, for emphasis in the agent prompt) but acceptance criterion uses `grep -c "statistical prior"` (lowercase, case-sensitive). Result: grep returned 0 instead of >=2.
- **Fix:** Changed "STATISTICAL PRIOR" to lowercase "statistical prior" in both Pitfall 6 and Section 5 Neighbours header.
- **Files modified:** .claude/agents/lucy-nmr-chemist.md
- **Commit:** fedb5cd (in same task commit)

**2. [Rule 1 - Bug] Case-sensitivity in Convergent/convergent and Renormalizing/renormalizing (lsd-engineer)**
- **Found during:** Task 2 verification
- **Issue:** Same pattern — "Convergent" (capital C) and "Renormalizing" (capital R) not matched by lowercase grep criteria.
- **Fix:** Changed to lowercase "convergent" and "renormalizing" in the FIX-10 PROHIBITION block.
- **Files modified:** .claude/agents/lucy-lsd-engineer.md
- **Commit:** 2388783 (in same task commit)

## Known Stubs

None. All three edits are complete, self-contained rule additions. No stubs or placeholders present.

## Threat Flags

No new security-relevant surface introduced. Files edited are agent prompt definitions (markdown), not network endpoints, auth paths, or schema definitions. The compound-agnostic guard (T-83-02) passed with 0 hits.

## Self-Check: PASSED

Files exist:
- FOUND: .planning/phases/83-constraint-hardness-guard/83-01-SUMMARY.md (this file)
- FOUND: .claude/agents/lucy-nmr-chemist.md (modified)
- FOUND: .claude/agents/lucy-lsd-engineer.md (modified)
- FOUND: .claude/agents/lucy-devils-advocate.md (modified)

Commits exist:
- fedb5cd: feat(83-01): nmr-chemist — full-distribution advisory rule + Pitfall 6 FIX-10
- 2388783: feat(83-01): lsd-engineer — FIX-10 PROHIBITION block + convergent-evidence rule
- d7b844b: feat(83-01): devils-advocate — G-PROP-EVIDENCE gate (FIX-10 constraint hardness guard)
