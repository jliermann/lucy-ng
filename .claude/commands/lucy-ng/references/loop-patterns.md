# Loop Detection Patterns Reference

<loop_detection_reference>

## Five Loop Patterns

Detailed definitions for the detect_loops step:

### ELIM Thrashing
**Definition:** Adding or removing ELIM repeatedly without diagnosing the root cause.

**Detection criteria:**
- ELIM added 2+ times across iterations
- OR: ELIM added, removed, then added again

**Common root causes:**
- sp2 count is odd (most common)
- Hydrogen budget mismatch
- 1J artifacts in HMBC
- Close carbons causing ambiguous assignment

### Zero-Solution Loop
**Definition:** Three or more consecutive iterations returning 0 solutions without changing approach.

**Detection criteria:**
- 3+ consecutive iterations with solution_count = 0
- Same approach (e.g., keep adding HMBC without removing any)

**Common root causes:**
- Conflicting HMBC correlations (1J artifacts)
- Incorrect carbon assignment (close peaks, overlapping signals)
- Incorrect molecular formula
- Close carbons within 3 ppm (digital resolution limit)

### Solution Explosion
**Definition:** Three or more consecutive iterations with solution count > 100 and < 10% reduction each.

**Detection criteria:**
- Last 3 iterations all have solution_count > 100
- Each iteration reduces count by less than 10% compared to previous

**Common root causes:**
- ELIM present (increases solution space)
- Added correlations are redundant (connecting already-connected atoms)
- Missing heteroatom constraints (O, N positions unspecified)
- Quaternary carbons with 0 HMBC correlations (not constraining structure)

### Constraint Churning
**Definition:** Adding and removing constraints randomly without convergence over 5+ iterations.

**Detection criteria:**
- Last 5 iterations show >10 constraints added AND >5 constraints removed
- Most recent iteration has solution_count > 50

**Common root causes:**
- Random correlation selection (not criteria-based)
- Not following incremental HMBC strategy
- Molecular formula incorrect (no strategy will converge)

### Quality Convergence Failure
**Definition:** Solutions converge to a small count but ALL top-K candidates are
IMPLAUSIBLE or QUESTIONABLE per the solution-analyst's verdict.

**Detection criteria (primary — check FIRST):**
- solution-analyst's most recent [RANKING-COMPLETE] record lists Chemical plausibility
  as "IMPLAUSIBLE" or "QUESTIONABLE" for ALL top-3 candidates.
- A [RANKING-COMPLETE] record for the current iteration must exist (guard against
  false fire before ranking has run).

**Detection criteria (OR trigger):**
- best MAE in latest [RANKING-COMPLETE] > 4.0 ppm AND solution_count ≤ 20.

**Common root causes:**
- A key peak was missed in initial 13C picking (e.g., weak quaternary carbonyl masked
  by a solvent-dominated max-relative threshold)
- DBE deficit: missing carbonyl → forced extra ring → correct structure excluded
- Para-symmetry not detected: 2C-equivalent aromatic peaks not passed to
  detect_aromatic_cosy_pairs → emergent ring mechanism never activated
- Incorrect molecular formula

**Why this is different from Patterns 1–4:**
Patterns 1–4 detect LSD-level symptoms (zero solutions, explosion, churning, ELIM thrash).
This pattern fires when LSD is healthy but the **interpretation going into LSD was wrong
from the start**. A solution_count of ≤ 20 looks like SUCCESS to the other patterns —
this is the characteristic false-convergence trap for this pattern.

**Budget:** Exactly 1 re-examination cycle. After that, honest termination.
Do NOT escalate to the diagnostic specialist (it is LSD-focused, not pick-focused).

</loop_detection_reference>
