---
phase: 79-peak-picking-symmetry-fix
plan: "03"
subsystem: agent-skills
tags: [skill-update, nmr-chemist, loop-patterns, case-orchestrator, advisory-templates, FIX-06]
dependency_graph:
  requires: [79-01, 79-02]
  provides: [FIX-06-layer2-feedback-loop]
  affects: [lucy-nmr-chemist.md, loop-patterns.md, case.md, advisory-templates.md]
tech_stack:
  added: []
  patterns: [mandatory-procedural-step, loop-pattern-detection, advisory-template]
key_files:
  created: []
  modified:
    - /Users/steinbeck/.claude/agents/lucy-nmr-chemist.md
    - /Users/steinbeck/.claude/commands/lucy-ng/references/loop-patterns.md
    - /Users/steinbeck/.claude/commands/lucy-ng/case.md
    - /Users/steinbeck/.claude/commands/lucy-ng/references/advisory-templates.md
decisions:
  - D-07/D-08/D-09/D-13: DBE self-check is MANDATORY procedural step but a diagnostic flag, not a decision gate — agent decides whether to act
  - D-10/D-11: Pattern 5 primary trigger = all top-3 IMPLAUSIBLE/QUESTIONABLE; OR-trigger = MAE > 4.0 AND count <= 20
  - D-12: QUALITY_CONVERGENCE_FAILURE budget = exactly 1 re-examination cycle, then honest termination
  - No diagnostic-specialist escalation for Pattern 5 (specialist is LSD-focused, not pick-focused)
metrics:
  duration: "~20 minutes"
  completed: "2026-06-08"
  tasks: 2
  files: 4
---

# Phase 79 Plan 03: Skill Wiring — DBE Self-Check + Pattern 5 Quality Convergence Failure

**One-liner:** Added mandatory DBE self-check (section 5a) and intensity-symmetry procedural steps to nmr-chemist skill, plus wired the 5th quality loop-pattern (QUALITY_CONVERGENCE_FAILURE) into case.md / loop-patterns.md / advisory-templates.md.

## What Was Built

### Task 1: nmr-chemist.md additions (3 targeted insertions)

**Insertion 1 — Intensity-Symmetry Check subsection** (added before "Run detection ONCE per compound" in section 5):
- 4-step procedure for aromatic CH intensity comparison
- 1.6x median threshold for 2C-equivalence candidates
- Feeds `lucy detect aromatic-cosy` with correct grouped shifts
- Labelled MANDATORY for aromatic compounds

**Insertion 2 — Section 5a: DBE Self-Check** (added between section 5 and section 6):
- Formula: DBE = (2C + 2 + N − H) / 2
- Covers O→carbonyl 160-220 ppm, N→amide/nitrile 150-180/100-120 ppm
- FLAG protocol for deficit cases (with SNR 3-20 check hint)
- Diagnostic flag, not a decision gate — per D-13

**Insertion 3 — [SETUP-COMPLETE] template fields** (after "Quality assessment:" line):
- `DBE balance: <accounted N of M DBE> or <deficit N DBE; suspected: region>`
- `Intensity-symmetry: <ppm: ratio, 2C candidate> or <none detected>`

**Workflow steps added:**
- Step 5a: intensity-symmetry check (MANDATORY for aromatic compounds)
- Step 6b: DBE self-check (MANDATORY before [SETUP-COMPLETE])

### Task 2: Loop-pattern 5 wired into three files

**loop-patterns.md:**
- Header updated from "Four Loop Patterns" to "Five Loop Patterns"
- New block "Quality Convergence Failure" appended before closing tag
  - Primary trigger: all top-3 IMPLAUSIBLE/QUESTIONABLE in [RANKING-COMPLETE]
  - OR-trigger: best MAE > 4.0 ppm AND solution_count <= 20
  - Guard: only fires if [RANKING-COMPLETE] record exists for current iteration
  - Budget: 1 cycle; no diagnostic-specialist escalation

**case.md detect_loops step:**
- Intro updated to "Five patterns to detect: ..."
- Pattern 5 criterion block inserted after Pattern 4, before convergence check

**case.md track_and_decide step:**
- `QUALITY_CONVERGENCE_FAILURE: count_quality` added to per-pattern counters list
- Decision block added: count_quality == 0 → advisory; count_quality >= 1 → honest termination

**advisory-templates.md:**
- New `<step name="quality_convergence_advisory">` block appended before `<anti_patterns>`
- Deliver to: nmr-chemist (NOT lsd-engineer)
- 3-item re-examination checklist: DBE balance, intensity-symmetry, multiplicity spot-check
- Explicit budget warning: "THIS IS THE ONLY re-examination cycle"
- After delivery: return to monitor_progress, wait for [DETECTION-COMPLETE]

## Grep Verification Results

### Task 1 assertions

```
grep -c "DBE Self-Check|Intensity-Symmetry Check|DBE balance|Intensity-symmetry" \
  /Users/steinbeck/.claude/agents/lucy-nmr-chemist.md
→ 9  (required: >= 6) PASS

grep -n "MANDATORY" /Users/steinbeck/.claude/agents/lucy-nmr-chemist.md
→ line 117: ### Intensity-Symmetry Check (MANDATORY for aromatic compounds)
→ line 156: ## 5a. DBE Self-Check (MANDATORY — before [SETUP-COMPLETE])
→ line 307: 5a. Perform intensity-symmetry check ... (MANDATORY for aromatic compounds)
→ line 310: 6b. Perform DBE self-check (Section 5a — MANDATORY before [SETUP-COMPLETE])
→ 4 matches (required: >= 2) PASS
```

### Task 2 assertions

```
grep -c "Quality Convergence Failure|QUALITY_CONVERGENCE_FAILURE" \
  loop-patterns.md → 1  (required: >= 1) PASS
  case.md         → 4  (required: >= 2) PASS
  advisory-templates.md → 2  (required: >= 1) PASS

grep -n "quality_convergence_advisory" advisory-templates.md
→ line 243: <step name="quality_convergence_advisory">
→ 1 match (required: 1) PASS

grep -n "count_quality" case.md
→ line 492: - QUALITY_CONVERGENCE_FAILURE: count_quality
→ line 506: - count_quality == 0: deliver assumption-reexamination advisory ...
→ line 507: - count_quality >= 1: honest termination ...
→ 3 matches (required: >= 2) PASS

grep -n "Pattern 5" case.md
→ line 360: **Pattern 5: Quality Convergence Failure** ...
→ 1 match (required: 1) PASS

grep -n "Five Loop Patterns|Five patterns to detect" loop-patterns.md case.md
→ loop-patterns.md line 5: ## Five Loop Patterns  PASS
→ case.md line 348: Five patterns to detect: ...  PASS
```

## Python Test Suite

```
1034 passed, 7 skipped, 1 xfailed, 33 warnings in 346.87s (0:05:46)
```

No regressions from markdown-only edits. `tests/test_intensity_symmetry.py` and `tests/test_peak_picker_snr.py` both GREEN (included in the 1034 passing).

## Deviations from Plan

None — plan executed exactly as written. All 4 files received targeted insertions per PATTERNS.md. No structural changes to existing skill sections.

## Status

Awaiting human-verify checkpoint approval. Tasks 1 and 2 complete; grep assertions all pass; Python suite green.

## Self-Check: PASSED

- /Users/steinbeck/.claude/agents/lucy-nmr-chemist.md: modified (DBE self-check + intensity-symmetry sections present)
- /Users/steinbeck/.claude/commands/lucy-ng/references/loop-patterns.md: modified (Quality Convergence Failure block present)
- /Users/steinbeck/.claude/commands/lucy-ng/case.md: modified (Pattern 5 + QUALITY_CONVERGENCE_FAILURE counter present)
- /Users/steinbeck/.claude/commands/lucy-ng/references/advisory-templates.md: modified (quality_convergence_advisory step present)
- Python test suite: 1034 passed, exit code 0
