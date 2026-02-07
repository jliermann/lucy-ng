---
phase: 24-supervisor-agent
plan: 01
subsystem: ai-supervision
tags: [supervisor, loop-detection, diagnostics, intervention, CASE-workflow, multi-agent]
requires:
  - 23-02-PLAN.md  # Confidence scoring framework provides assessment criteria
  - 22-01-PLAN.md  # HMBC strategy and iteration cap feed into supervisor logic
  - 21-02-PLAN.md  # skill/supervisor/SKILL.md foundation (78 lines)
provides:
  - Complete supervisor domain knowledge (678 lines)
  - Four loop detection patterns with diagnostics (SUPV-02-05)
  - Advisory intervention model (SUPV-06)
  - Escalation protocol (SUPV-07)
  - CASE-PROGRESS.md format specification
affects:
  - 24-02-PLAN.md  # Supervisor agent definition will reference this skill
  - 25-*-PLAN.md   # Diagnostic specialist will integrate with this supervision framework
tech-stack:
  added: []
  patterns:
    - Multi-agent checkpoint-based communication (markdown progress logs)
    - Advisory intervention (constraints not directives)
    - Per-pattern intervention tracking
key-files:
  created: []
  modified:
    - skill/supervisor/SKILL.md  # Expanded from 78 to 678 lines
    - skill/CASE/SKILL.md        # Added Step 7c for checkpoint writing
decisions:
  - decision: "Advisory intervention model: supervisor tells CASE agent WHAT to fix, not HOW"
    rationale: "Preserves CASE agent autonomy while providing diagnostic constraints"
    location: "skill/supervisor/SKILL.md Section 3"
  - decision: "Escalate after 10 failed intervention cycles per pattern (not 3)"
    rationale: "Per CONTEXT.md: give supervisor substantial room to try different angles"
    location: "skill/supervisor/SKILL.md Section 6"
  - decision: "Track intervention count per pattern, not globally"
    rationale: "Different patterns have different root causes; prevents premature escalation"
    location: "skill/supervisor/SKILL.md Section 6"
  - decision: "Markdown format for CASE-PROGRESS.md (not JSON)"
    rationale: "AI agents parse natural language better; includes reasoning ('WHY' field)"
    location: "skill/supervisor/SKILL.md Section 7"
  - decision: "Append-only progress log (never overwrite)"
    rationale: "Supervisor needs full iteration history to detect patterns across iterations"
    location: "skill/supervisor/SKILL.md Section 7"
metrics:
  duration: "4m 11s"
  completed: "2026-02-07"
---

# Phase 24 Plan 01: Supervisor Skill Expansion Summary

**One-liner:** Expanded supervisor skill from 78 to 678 lines with four loop detection patterns (ELIM thrashing, zero-solution loop, solution explosion, constraint churning), diagnostic procedures, advisory intervention model, escalation protocol, and complete CASE-PROGRESS.md checkpoint format.

---

## What Was Built

### 1. Expanded supervisor/SKILL.md (78 → 678 lines)

Complete supervisor domain knowledge with 7 sections:

1. **Overview and Role** — Supervisor as single entry point, CASE supervision architecture, advisory intervention model
2. **Routing Logic** — Decision tree for routing to sanitize/dereplication/CASE
3. **CASE Workflow Supervision** — Spawning CASE agent, monitoring progress, advisory constraints
4. **Loop Detection Patterns** — Four patterns (SUPV-02-05) with detection criteria, diagnostics, and advisory messages
5. **Convergence Criteria** — Solution count trends, constraint effectiveness, flexible success targets, safety cap
6. **Intervention Tracking and Escalation** — Per-pattern tracking, intervention cycle, escalation after 10 cycles
7. **CASE-PROGRESS.md Format Specification** — Complete format with 3-iteration example

### 2. Updated CASE/SKILL.md

Added **Step 7c: Write Progress Checkpoint** with:
- Instructions to write CASE-PROGRESS.md after EVERY LSD iteration
- Format template with all required fields
- Append-only rule
- Cross-reference to supervisor/SKILL.md Section 7 for complete specification

Added **supervisor integration note** at top of Workflow section.

---

## Loop Detection Patterns

### 4.1 ELIM Thrashing (SUPV-02)

**Detection:** ELIM added/removed 2+ times without diagnosis

**Diagnostics:**
1. Check sp2 count is even (skill/SKILL.md Section 5.3)
2. Check hydrogen budget matches formula
3. Check for 1J artifacts in HMBC (skill/SKILL.md Section 2.3)
4. Check for close carbons causing ambiguous assignment

**Advisory:** Directs CASE agent to verify sp2/H budget/1J artifacts before retrying; forbids ELIM until checks pass

### 4.2 Zero-Solution Loop (SUPV-03)

**Detection:** 3+ consecutive iterations with 0 solutions, same approach

**Diagnostics:**
1. Remove last batch, confirm solutions return
2. Test individual correlations to find conflict
3. Check for 1J artifacts
4. Check for close carbons (digital resolution issue)
5. Check molecular formula correctness

**Advisory:** Directs CASE agent to remove last batch, test individually, resolve conflict

### 4.3 Solution Explosion (SUPV-04)

**Detection:** 3+ iterations with >100 solutions and <10% reduction each

**Diagnostics:**
1. Check if ELIM is present (remove it)
2. Check if correlations are actually constraining (not redundant)
3. Check quaternary carbons (skill/SKILL.md Section 10.3)
4. Check heteroatom constraints (BOND or LIST/PROP)

**Advisory:** Directs CASE agent to remove ELIM, verify correlations connect NEW fragments, add heteroatom/quaternary constraints

### 4.4 Constraint Churning (SUPV-05)

**Detection:** 5+ iterations with high add/remove activity (>10 added, >5 removed) and no convergence (>50 solutions)

**Diagnostics:**
1. Check if systematic strategy is being followed (skill/SKILL.md Section 7)
2. Check if correlations selected by criteria or randomly
3. Check molecular formula correctness

**Advisory:** Directs CASE agent to reset to last known-good state, follow incremental HMBC strategy with criteria-based selection

---

## Advisory Intervention Model (SUPV-06)

**Principle:** Supervisor tells CASE agent WHAT the problem is and WHAT to fix, but NOT exactly HOW to fix it.

**Example (advisory):**
```
ELIM thrashing detected. Before retrying:
1. Verify sp2 count is even
2. Verify H budget matches formula
3. Check last HMBC batch for 1J artifacts

Do NOT add ELIM again until all checks pass.
```

**NOT directive:**
```
Change line 15 of compound.lsd from "MULT 5 C 2 1" to "MULT 5 C 3 1".
```

**Rationale:** CASE agent retains autonomy while getting diagnostic constraints.

---

## Escalation Protocol (SUPV-07)

**Per-pattern tracking:** Intervention count tracked separately for each of the 4 loop patterns.

**Intervention cycle:**
1. Detect loop pattern from CASE-PROGRESS.md
2. Diagnose root cause using pattern-specific procedure
3. Advise CASE agent with specific constraints
4. Increment intervention counter for this pattern
5. CASE agent retries
6. Supervisor monitors next iteration

**Escalation trigger:** 10 failed intervention cycles with SAME pattern (per CONTEXT.md decision, overrides initial "3 cycles" from foundation document).

**Non-pattern escalation:** Immediate escalation for conflicting data, unusual shifts, formula mismatch.

---

## CASE-PROGRESS.md Format

**Purpose:** Communication interface between CASE agent and supervisor.

**Format:** Markdown with structured sections (human-readable, AI-parseable).

**Location:** Compound's working directory.

**Rule:** Append-only (each iteration APPENDS; NEVER overwrite).

**Required fields per iteration:**
- Iteration N: description
- Time
- LSD file
- Solution count
- Constraints added (with reasoning)
- Constraints removed (with reasoning)
- Why (natural language explanation of strategy)
- Constraint effectiveness
- Confidence
- HMBC correlations used (X/Y)
- Notes (sp2 check, H budget, observations)

**Example included:** 3-iteration log showing baseline, productive batch, and failure recovery.

---

## Convergence Criteria

**Solution count trends:** Should decrease over iterations.

**Constraint effectiveness:**
- Effective: ≥30% reduction
- Marginally effective: 10-30%
- Ineffective: <10%
- Over-constrained: 0 solutions

**Flexible success targets:**
- Ideal: 1-5 solutions with high confidence
- Acceptable: <10 solutions with good ranking differentiation
- Conditional: 10-20 if MAE gap ≥2 ppm between rank 1 and rank 2

**Hard safety cap:** ~20 total LSD iterations maximum.

**Plateau handling:**
- At ≤10 solutions with good ranking → convergence (STOP)
- At >10 solutions → try additional strategies (heteroatom constraints, symmetry, different HMBC batch)

---

## Cross-References

The supervisor skill document properly delegates domain knowledge to skill/SKILL.md:

| Supervisor Reference | Main SKILL.md Section |
|---------------------|----------------------|
| sp2 hybridization rules | Section 5.3 |
| 1J artifact detection | Section 2.3 |
| Incremental HMBC strategy | Section 7 |
| Quaternary carbon handling | Section 10.3 |
| Ambiguity encoding (LIST/PROP) | Section 10.2 |
| Digital resolution impact | Section 2.2 |
| Ranking and prediction | Section 8 |
| Confidence scoring | Section 11 |

**Total cross-references:** 17 (verified via grep).

**Zero domain knowledge duplication** — supervisor skill focuses on orchestration and loop detection; main skill contains NMR and CASE methodology.

---

## Deviations from Plan

None — plan executed exactly as written.

---

## Commits

| Commit | Message | Files |
|--------|---------|-------|
| efc3e13 | docs(24-01): expand supervisor skill with loop detection and diagnostics | skill/supervisor/SKILL.md |
| a6e6d06 | docs(24-01): add CASE-PROGRESS.md checkpoint writing to CASE workflow | skill/CASE/SKILL.md |

---

## Next Phase Readiness

**Phase 24 Plan 02 (Supervisor Agent Definition)** is ready:
- skill/supervisor/SKILL.md provides complete domain knowledge (678 lines)
- All four loop detection patterns (SUPV-02-05) fully specified
- Advisory intervention model (SUPV-06) documented
- Escalation protocol (SUPV-07) defined
- CASE-PROGRESS.md format specification complete

The supervisor agent definition can now reference this skill document for all orchestration and diagnostic knowledge.

**Phase 25 (Diagnostic Specialist)** foundation ready:
- Supervisor skill includes basic diagnosis procedures
- Clear delegation points identified for future diagnostic specialist
- Intervention cycle documented for integration

---

## Lessons Learned

### What Worked Well

1. **Structured expansion** — 7-section organization made the 678-line document highly navigable
2. **Detection criteria tables** — Compact presentation of loop pattern triggers
3. **Cross-referencing strategy** — 17 references to main SKILL.md prevented duplication while maintaining supervisor focus
4. **Example-driven format** — 3-iteration CASE-PROGRESS.md example makes format immediately clear
5. **Per-pattern tracking** — More precise than global intervention counter; prevents premature escalation

### What Could Be Better

1. **Format verbosity** — CASE-PROGRESS.md with all required fields is verbose (~50 lines per iteration for detailed logs); may need compression for long CASE runs
2. **Diagnostic procedure detail** — Some procedures (e.g., "test each correlation individually") could benefit from more specific guidance
3. **Convergence criteria edge cases** — "10-20 solutions MAY be acceptable if..." leaves judgment to supervisor; could be more prescriptive

### For Future Reference

- Markdown checkpoint format is well-suited for AI-to-AI communication (natural language + structure)
- Advisory model (constraints not directives) balances guidance with agent autonomy
- Per-pattern tracking prevents cross-contamination of intervention strategies
- 10-cycle escalation cap is generous; may need adjustment based on real-world usage

---

*Summary completed: 2026-02-07*
*Execution duration: 4m 11s*
