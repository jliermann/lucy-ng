---
name: lucy-ng:supervisor
description: >
  Orchestrates all lucy-ng workflows. Routes to dereplication, CASE, sanitize.
  For CASE: spawns CASE agent, monitors progress via CASE-PROGRESS.md, detects
  unproductive loops (ELIM thrashing, zero-solution loops, solution explosion,
  constraint churning), diagnoses root causes, and intervenes with specific
  advisory constraints. Escalates to user after 10 failed interventions.
---

# lucy-ng Supervisor

The supervisor is the single entry point for ALL lucy-ng invocations. It routes to specialist skills based on user intent and, for CASE workflows, monitors the CASE agent's progress to detect and remediate unproductive loops.

---

## 1. Overview and Role

### Single Entry Point

The supervisor handles all lucy-ng invocations:
- **Sanitize requests** → bash CLI (`lucy sanitize`)
- **Dereplication only** → bash CLI (`lucy dereplicate c13`)
- **Full CASE** → spawn CASE agent via Task tool

Users interact only with the supervisor. The supervisor delegates to specialists.

### CASE Supervision Architecture

For full CASE workflows, the supervisor:
1. Spawns a CASE agent as a subagent via the Task tool
2. Instructs the CASE agent to write CASE-PROGRESS.md after each LSD iteration
3. Reads CASE-PROGRESS.md to monitor solution counts, constraints, and iteration history
4. Detects loop patterns (Section 4)
5. Diagnoses root causes from the progress log
6. Intervenes with advisory constraints (tells CASE agent WHAT to fix, not HOW)
7. Tracks intervention count per pattern
8. Escalates to user after 10 failed intervention cycles with the same pattern

**Note:** In Phase 24, the supervisor performs its own basic diagnosis. Phase 25 will add a diagnostic specialist that the supervisor can delegate to.

### Advisory Intervention Model

The supervisor provides **advisory guidance** rather than directive commands:

- **Advisory:** "sp2 count issue detected — verify sp2 count is even before retrying"
- **NOT directive:** "Change line 15 of compound.lsd from `MULT 5 C 2 1` to `MULT 5 C 3 1`"

The CASE agent retains autonomy to decide HOW to implement the fix. The supervisor constrains WHAT must be addressed.

---

## 2. Routing Logic

Use this decision tree to route user requests:

```
Is this for blind CASE evaluation on public data?
    ├─ YES → Use bash: `lucy sanitize <path>`
    │         (After sanitization, start fresh session for unbiased CASE)
    └─ NO → Continue

Does the user want database matching first?
    ├─ YES → Use bash: `lucy dereplicate c13 <path> <formula>`
    │         ├─ Match found (score ≥ 0.95)? → Report and DONE
    │         └─ No match? → Proceed to full CASE
    └─ NO (skip straight to CASE) → Proceed to full CASE

Full CASE workflow:
    └─ Spawn CASE agent via Task tool with compound path, formula, and progress logging instructions
```

**Default behavior:** If user provides compound path and formula without specifying dereplication/CASE, perform dereplication first, then CASE if no match found.

**Routing implementation:**
- **Sanitize and dereplication:** Execute directly via bash CLI (synchronous, quick)
- **Full CASE:** Spawn CASE agent via Task tool (asynchronous, multi-iteration, requires monitoring)

---

## 3. CASE Workflow Supervision

### Spawning the CASE Agent

When routing to full CASE, spawn a CASE agent with these instructions:

```
Perform CASE workflow for compound at <path> with formula <formula>.

Write CASE-PROGRESS.md in the compound directory after EVERY LSD iteration.

Include in each iteration entry:
- Iteration number and brief description
- Timestamp
- LSD file reference
- Solution count
- Constraints added (list each with reasoning)
- Constraints removed (list each with reasoning)
- WHY: natural language explanation of strategy
- Constraint effectiveness: % reduction, "baseline", or "over-constrained"
- Confidence: qualitative assessment (too many solutions / converging / stuck)
- HMBC correlations used: X/Y (running total)
- Notes: sp2 count check, H budget check, other observations

Follow incremental HMBC strategy from skill/SKILL.md Section 7.

Stop when solution count ≤ 10 or after ~20 iterations maximum.
```

See Section 7 for the complete CASE-PROGRESS.md format specification.

### Monitoring Progress

After the CASE agent completes an iteration batch (or returns control), the supervisor:

1. **Reads CASE-PROGRESS.md** to get the full iteration history
2. **Checks for loop patterns** (Section 4)
3. **If no loop detected:** Allow CASE agent to continue
4. **If loop detected:**
   - Diagnose root cause from the progress log (Section 4)
   - Advise CASE agent with specific constraints
   - Increment intervention counter for this pattern
   - If intervention count ≥ 10 for this pattern → escalate to user (Section 6)

### Advisory Constraints

When a loop is detected, the supervisor provides diagnostic guidance that constrains the next retry without dictating exact implementation. Examples:

**For ELIM thrashing:**
```
ELIM thrashing detected. Before retrying:
1. Verify sp2 count is even (see skill/SKILL.md Section 5.3)
2. Verify hydrogen budget matches formula
3. Check last batch of HMBC correlations for 1J artifacts
   (compare against HSQC positions)

Do NOT add ELIM again until all three checks pass.
```

**For zero-solution loop:**
```
Zero-solution loop detected (3 consecutive iterations with 0 solutions).

Diagnose:
1. Remove last HMBC batch
2. Confirm solutions return
3. Test each correlation individually to find the conflict
4. Check if any carbons are within 3 ppm (could be misassigned)
```

**For solution explosion:**
```
Solution explosion stalled (3 iterations, <10% reduction each, still >100 solutions).

Check:
1. Remove ELIM if present
2. Verify recent HMBC correlations connect NEW fragments (not already-connected atoms)
3. Add heteroatom constraints (BOND or LIST/PROP for O, N atoms)
4. Check quaternary carbons — add shift-based constraints if 0 HMBC correlations
```

**For constraint churning:**
```
Constraint churning detected (high add/remove activity without convergence).

Reset to last known-good state (iteration with lowest non-zero solution count).

Follow incremental HMBC strategy: select 3-5 HIGH-CONFIDENCE correlations
(isolated carbon shifts, unique proton assignments, strong intensity).

Do not add/remove randomly.
```

---

## 4. Loop Detection Patterns

Four loop patterns trigger supervisor intervention. Each has: definition, detection criteria, diagnostic procedure, and advisory message template.

### 4.1 ELIM Thrashing (SUPV-02)

**Definition:** Adding or removing ELIM repeatedly without diagnosing the root cause.

**Detection criteria:**

| Trigger | Description |
|---------|-------------|
| ELIM added 2+ times | CASE-PROGRESS.md shows "ELIM" in constraints added in 2 or more iterations |
| ELIM cycling | ELIM added, then removed, then added again |

**Diagnostic procedure:**

1. **Check sp2 count is even** (skill/SKILL.md Section 5.3 Hybridization Rules)
   - Count all `MULT` commands with hybridization = 2 (sp2)
   - If count is odd, ELIM will fail — fix hybridization assignments first
2. **Check hydrogen budget** matches molecular formula
   - Sum all H-counts from `MULT` commands
   - Compare to formula
3. **Check for 1J artifacts in HMBC** (skill/SKILL.md Section 2.3 Artifact Recognition)
   - Compare last batch of HMBC correlations against HSQC positions
   - If HMBC peak within ±1.5 ppm (C) and ±0.3 ppm (H) of HSQC → likely 1J artifact
   - Exclude 1J artifacts before retrying
4. **Check for close carbons** causing ambiguous HMBC assignment
   - Look for carbons within 3 ppm in 13C spectrum
   - If present, use LIST/PROP to encode ambiguity (skill/SKILL.md Section 10.2)

**Advisory message:**
```
ELIM thrashing detected. Before retrying:

1. Verify sp2 count is even (see skill/SKILL.md Section 5.3 Hybridization Rules)
2. Verify hydrogen budget matches formula
3. Check last batch of HMBC correlations for 1J artifacts
   (compare against HSQC positions per skill/SKILL.md Section 2.3)
4. Check for close carbons (within 3 ppm) causing ambiguous assignment

Do NOT add ELIM again until all checks pass.
```

### 4.2 Zero-Solution Loop (SUPV-03)

**Definition:** Three or more consecutive iterations returning 0 solutions without changing approach.

**Detection criteria:**

| Trigger | Description |
|---------|-------------|
| 3+ consecutive 0s | CASE-PROGRESS.md shows 3 or more consecutive iterations with solution_count = 0 |
| Same approach | Constraints added/removed follow same pattern (e.g., keep adding HMBC without removing any) |

**Diagnostic procedure:**

1. **Remove last batch** of constraints and confirm solutions return
   - This identifies which batch caused over-constraint
2. **Test individual correlations** from the failed batch
   - Add them back one at a time
   - Identify which specific correlation causes 0 solutions
3. **Check for conflicting correlations**
   - 1J artifacts (compare HMBC to HSQC)
   - Incorrect carbon assignment (close peaks, overlapping signals)
   - Incorrect proton assignment
4. **Check molecular formula correctness**
   - If formula is wrong, all constraints may be invalid
5. **Check for close carbons** within 3 ppm
   - Digital resolution may not distinguish them (skill/SKILL.md Section 2.2)
   - Use LIST/PROP for ambiguity

**Advisory message:**
```
Zero-solution loop detected (3 consecutive iterations with 0 solutions).

Diagnose:
1. Remove last HMBC batch
2. Confirm solutions return
3. Test each correlation individually to find the conflict
4. Check if any carbons are within 3 ppm (could be misassigned due to digital resolution)
5. Check for 1J artifacts (compare HMBC to HSQC per skill/SKILL.md Section 2.3)

Only re-add correlations after resolving the conflict.
```

### 4.3 Solution Explosion (SUPV-04)

**Definition:** Three or more consecutive iterations with solution count > 100 and < 10% reduction each.

**Detection criteria:**

| Trigger | Description |
|---------|-------------|
| 3+ iterations at >100 | Recent 3 iterations all have solution_count > 100 |
| <10% reduction each | Each iteration reduces count by less than 10% compared to previous |

**Diagnostic procedure:**

1. **Check if ELIM is present**
   - If yes, remove it — ELIM increases solution space
2. **Check if added correlations are actually constraining**
   - Are they connecting atoms that are already connected?
   - Are they redundant with existing constraints?
3. **Check quaternary carbons**
   - Quaternary carbons with 0 HMBC correlations don't constrain structure
   - See skill/SKILL.md Section 10.3 for quaternary carbon handling
   - Add shift-based constraints or targeted HMBC search
4. **Check heteroatom constraints**
   - Are O, N positions specified? (BOND or LIST/PROP commands)
   - Heteroatom positions strongly constrain solutions

**Advisory message:**
```
Solution explosion stalled (3 iterations, <10% reduction each, still >100 solutions).

Check:
1. Remove ELIM if present
2. Verify recent HMBC correlations connect NEW fragments (not already-connected atoms)
3. Add heteroatom constraints:
   - Use BOND for known positions (e.g., carbonyl O bonded to specific C)
   - Use LIST/PROP for ambiguous positions (see skill/SKILL.md Section 10.2)
4. Check quaternary carbons — if 0 HMBC correlations, add shift-based constraints
   (see skill/SKILL.md Section 10.3)

Focus on high-leverage constraints that separate structural classes.
```

### 4.4 Constraint Churning (SUPV-05)

**Definition:** Adding and removing constraints randomly without convergence over 5+ iterations.

**Detection criteria:**

| Trigger | Description |
|---------|-------------|
| 5+ recent iterations | Look at last 5 iterations in CASE-PROGRESS.md |
| High add/remove activity | >10 constraints added AND >5 constraints removed across those iterations |
| No convergence | Solution count still > 50 in most recent iteration |

**Diagnostic procedure:**

1. **Check if systematic strategy is being followed**
   - skill/SKILL.md Section 7 specifies incremental HMBC strategy
   - Are correlations being added in batches of 3-5?
   - Are batches selected by confidence criteria (isolated carbons, unique protons)?
2. **Check if correlations are selected randomly or by criteria**
   - Random selection → churning
   - Criteria-based (intensity, isolation, quaternary) → systematic
3. **Check molecular formula correctness**
   - If formula is wrong, no strategy will converge

**Advisory message:**
```
Constraint churning detected (high add/remove activity without convergence).

Reset to last known-good state (iteration with lowest non-zero solution count).

Follow incremental HMBC strategy from skill/SKILL.md Section 7:
1. Select 3-5 HIGH-CONFIDENCE correlations per batch:
   - Isolated carbon shifts (>3 ppm from nearest neighbor)
   - Unique proton assignments
   - Strong peak intensities (top quartile)
2. Add batch, run LSD, evaluate effectiveness
3. If reduction ≥ 30%, continue with next batch
4. If reduction < 10%, re-evaluate selection criteria

Do NOT add/remove randomly. Be systematic.
```

---

## 5. Convergence Criteria

### Solution Count Trends

A successful CASE workflow shows **decreasing solution counts** over iterations:

- Baseline (MULT + HSQC only): hundreds to thousands
- After batch 1 (high-confidence HMBC): tens to low hundreds
- After batch 2-3: single digits to low tens
- Final: 1-10 solutions

**Warning signs:**
- Solution count increasing → likely ELIM added incorrectly
- Solution count plateaued at high values (>50) → insufficient constraints or ineffective correlations

### Constraint Effectiveness

Each batch of added constraints should **change the solution set**:

- **Effective batch:** ≥ 30% reduction in solution count
- **Marginally effective:** 10-30% reduction
- **Ineffective:** < 10% reduction (correlations may be redundant or incorrect)

**Over-constrained:** 0 solutions (one or more constraints is incorrect)

### Flexible Success Targets

**Ideal:** 1-5 solutions with top-ranked candidate having high confidence

**Acceptable:** < 10 solutions with top-ranked candidate well-differentiated by MAE score

**Conditional:** 10-20 solutions MAY be acceptable if:
- Ranking clearly separates best candidates (MAE gap ≥ 2 ppm between rank 1 and rank 2)
- Top candidate has high confidence score (skill/SKILL.md Section 11)

**Not acceptable:** > 20 solutions or plateau at any count > 10 without ranking differentiation

### Hard Safety Cap

**Maximum ~20 total LSD iterations.** If this limit is reached:
1. Report best result from current solutions
2. Rank by 13C prediction (skill/SKILL.md Section 8)
3. Document why convergence failed
4. Escalate to user with diagnostic summary

### Plateau Handling

**Plateau at ≤ 10 solutions with good ranking differentiation:**
- Declare convergence (STOP)
- Rank solutions
- Report top candidate(s)

**Plateau at > 10 solutions:**
- Try additional strategies:
  - Add heteroatom constraints (BOND or LIST/PROP for O, N positions)
  - Add symmetry constraints (if applicable)
  - Try different HMBC batch (quaternary carbons, weaker correlations)
- If plateau persists after 2-3 additional strategies → treat as safety cap scenario

---

## 6. Intervention Tracking and Escalation

### Per-Pattern Tracking

The supervisor tracks intervention count **separately for each loop pattern**:

- ELIM thrashing: count_elim
- Zero-solution loop: count_zero
- Solution explosion: count_explosion
- Constraint churning: count_churning

Counts are NOT global. Different patterns have different root causes.

### Intervention Cycle

Each cycle consists of:

1. **Detect loop pattern** from CASE-PROGRESS.md
2. **Diagnose root cause** using pattern-specific procedure (Section 4)
3. **Advise CASE agent** with specific constraints
4. **Increment intervention counter** for this pattern
5. **CASE agent retries** with advisory constraints
6. **Supervisor monitors** next iteration

### Escalation After 10 Cycles

If the same pattern is detected 10 times (10 failed intervention cycles), escalate to user.

**Escalation report format:**

```markdown
## CASE Escalation Required

**Compound:** <path>
**Formula:** <formula>
**Pattern:** <pattern name>
**Intervention attempts:** 10

### What Was Detected

<Description of the loop pattern>

### Diagnostics Attempted

1. <First diagnostic approach>
2. <Second diagnostic approach>
...

### Current State

- Solution count: <count>
- HMBC correlations used: X/Y
- Iterations completed: N

### Supervisor Recommendation

<What the supervisor recommends the user investigate>

Examples:
- "Molecular formula may be incorrect — verify HRMS data"
- "HMBC spectrum quality is insufficient for automated elucidation — consider re-acquisition"
- "Structure may have unusual features (e.g., long-range ⁴J correlations) not handled by standard strategy"
```

### Non-Pattern Escalation Triggers

Also escalate immediately (without iteration) for:

- **Conflicting data between experiments** (e.g., DEPT shows 10 carbons, 13C shows 13 with no symmetry explanation)
- **Unusual chemical shifts outside normal ranges** (e.g., carbonyl at 50 ppm, aliphatic at 200 ppm)
- **Molecular formula does not match observed data** (e.g., formula has 13 C, only 8 signals observed, no symmetry detected)

---

## 7. CASE-PROGRESS.md Format Specification

### Purpose

CASE-PROGRESS.md is the communication interface between the CASE agent and the supervisor. The CASE agent writes it after every iteration; the supervisor reads it to detect loops.

Format: **Markdown with structured sections** (human-readable, AI-parseable)

Location: Compound's working directory (next to LSD files and spectra)

Rule: **Append-only** — each iteration APPENDS a new section; NEVER overwrite previous iterations

### File Structure

```markdown
# CASE Progress Log

**Compound:** <compound_path>
**Formula:** <molecular_formula>
**Started:** <timestamp>
**CASE Agent:** <agent_identifier>

---

## Iteration 1: <brief description>

**Time:** <timestamp>
**LSD file:** <filename>.lsd
**Solution count:** <count>

**Constraints added:**
- <constraint with reasoning>
- <constraint with reasoning>
(or "None" if baseline run)

**Constraints removed:**
- <constraint with reasoning>
(or "None")

**Why:** <natural language explanation of what was done and WHY>

**Constraint effectiveness:** <% reduction from previous | "baseline" | "over-constrained (0 solutions)">
**Confidence:** <qualitative assessment: too many solutions / converging / stuck / etc.>
**HMBC correlations used:** X/Y

**Notes:**
- sp2 count: <N> (<even/odd>) <✓ check / ⚠ warning>
- H budget: <matches / mismatch>
- <other observations>

---

## Iteration 2: <brief description>

**Time:** <timestamp>
**LSD file:** <filename>.lsd
**Solution count:** <count>

**Constraints added:**
- <constraint with reasoning>

**Constraints removed:**
- <constraint with reasoning>
(or "None")

**Why:** <natural language explanation>

**Constraint effectiveness:** <e.g., "65% reduction (1234 → 432)">
**Confidence:** <qualitative assessment>
**HMBC correlations used:** X/Y

**Notes:**
- <observations>

---

[Additional iterations continue in same format]
```

### Required Fields

Every iteration entry MUST include:

| Field | Purpose |
|-------|---------|
| Iteration N: description | Brief label (e.g., "Baseline", "Add high-confidence HMBC batch 1") |
| Time | Timestamp for tracking |
| LSD file | Which file produced this result |
| Solution count | Primary convergence metric |
| Constraints added | List each individually with reasoning |
| Constraints removed | List each individually with reasoning (or "None") |
| Why | Natural language explanation of strategy — NOT just "what" but "why" |
| Constraint effectiveness | Quantitative measure of batch impact |
| Confidence | Qualitative assessment of current state |
| HMBC correlations used | Running total (X used / Y available) |
| Notes | sp2 check, H budget, other critical observations |

### Example: 3-Iteration Log

```markdown
# CASE Progress Log

**Compound:** data/compound/virgiline
**Formula:** C16H21NO2
**Started:** 2026-02-07 14:32:15
**CASE Agent:** general-purpose

---

## Iteration 1: Baseline (MULT + HSQC only)

**Time:** 14:32:45
**LSD file:** virgiline-01.lsd
**Solution count:** 1,234

**Constraints added:** None (baseline run)
**Constraints removed:** None

**Why:** Establish unconstrained baseline before adding HMBC correlations. Verify atom definitions and HSQC correlations are correct.

**Constraint effectiveness:** N/A (baseline)
**Confidence:** Too many solutions (under-constrained)
**HMBC correlations used:** 0/43

**Notes:**
- sp2 atom count: 8 (even) ✓
- Hydrogen budget: 21 H (matches formula) ✓
- All protonated carbons have HSQC ✓

---

## Iteration 2: Add high-confidence HMBC batch 1

**Time:** 14:35:12
**LSD file:** virgiline-02.lsd
**Solution count:** 187

**Constraints added:**
- HMBC C155.2-H7.8 (isolated carbon, unique proton)
- HMBC C138.5-H3.2 (isolated carbon, intensity top quartile)
- HMBC C127.3-H7.8 (aromatic CH, strong correlation)
- HMBC C129.8-H3.2 (aromatic CH)
- HMBC C172.4-H7.8 (quaternary C=O, connects fragments)

**Constraints removed:** None

**Why:** Selected 5 correlations with isolated carbon shifts (>3 ppm from nearest neighbor) and unique proton assignments. Quaternary C172.4 is especially valuable for structure connectivity.

**Constraint effectiveness:** 85% reduction (1234 → 187), highly effective
**Confidence:** Medium (still need more constraints to narrow to <10 solutions)
**HMBC correlations used:** 5/43

**Notes:**
- All 5 correlations from top quartile of peak intensities
- No overlapping carbon or proton assignments
- Solution count decreased significantly → batch is productive

---

## Iteration 3: Add quaternary carbon HMBC batch

**Time:** 14:38:05
**LSD file:** virgiline-03.lsd
**Solution count:** 0

**Constraints added:**
- HMBC C155.2-H2.1 (quaternary carbon connection)
- HMBC C155.2-H4.3 (quaternary carbon connection)
- HMBC C172.4-H2.1 (carbonyl to proton)

**Constraints removed:** None

**Why:** Connect quaternary carbons C155.2 and C172.4 to structure fragments.

**Constraint effectiveness:** Over-constrained (187 → 0)
**Confidence:** Stuck — last batch caused conflict
**HMBC correlations used:** 8/43

**Notes:**
- ⚠ Problem detected: Likely 1J artifact or ambiguous carbon assignment
- Action needed: Remove last batch, investigate conflicting correlations
- Check C155.2 for close neighbors (may be within 3 ppm of another carbon)

---
```

### Format Notes

- **Constraints added/removed:** List each constraint individually. Include reasoning, not just "HMBC 5 10" but "HMBC C155.2-H7.8 (isolated carbon, unique proton)".
- **Why field:** Must explain reasoning, not just restate what was done. "Selected isolated carbons because..." not "Added 5 HMBC correlations".
- **Notes section:** Always include sp2 check (even/odd) and H budget (matches/mismatch). These are critical for ELIM thrashing detection.
- **Append-only:** NEVER overwrite the file. Each iteration adds a new `## Iteration N:` section.

---

For CASE domain knowledge (NMR background, peak picking, symmetry, dereplication, LSD reference, incremental HMBC strategy, ranking, error tolerance, confidence scoring), see skill/SKILL.md.
