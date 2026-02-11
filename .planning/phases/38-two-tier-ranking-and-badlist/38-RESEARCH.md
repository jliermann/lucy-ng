---
phase: 38-two-tier-ranking-and-badlist
researched: 2026-02-11
researcher: Claude (gsd-phase-researcher)
confidence: HIGH
---

# Phase 38 Research: Two-Tier Ranking and Badlist

**Goal:** Solution ranking prevents MAE hallucinations and badlist excludes strained rings

## Executive Summary

Phase 38 implements two algorithmic improvements to prevent wrong solutions from ranking highly:

1. **Two-tier ranking** (RANK-01, RANK-02): Change sort order from MAE-only to (match_count DESC, MAE ASC)
2. **Badlist patterns** (RANK-03, RANK-04): Document 3/4-membered ring SMARTS patterns for LSD DEFF/FEXP NOT commands
3. **HOSE radius transparency** (implied by RANK-05): Already implemented — `PredictedShift.radius_used` exists

This is a **LOW-MEDIUM effort phase** (3-5 days):
- Two-tier ranking: Algorithmic change to existing `SolutionRanker` (1-2 days)
- Badlist patterns: Documentation in CASE agent knowledge (1 day)
- Integration testing: Verify ibuprofen hallucination is fixed (1-2 days)

**Critical insight from Sherlock analysis:** Lucy-ng's MAE-only ranking caused the ibuprofen hallucination (cyclohexadiene solutions had MAE 1.93 ppm which appeared "excellent"). Two-tier ranking counts signal matches BEFORE considering MAE, preventing this failure mode.

---

## 1. Existing Architecture Analysis

### 1.1 Current Ranking Implementation

**File:** `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/ranking/ranker.py`

**Key findings:**

```python
# Line 95: Current sort logic (WRONG ORDER)
ranked.sort(key=lambda r: (r.mae, -r.matched_count))
```

**Problem:** This sorts by MAE first, then match count as tiebreaker. A solution with MAE 1.93 and 11/13 matches will rank ABOVE a solution with MAE 2.13 and 13/13 matches.

**What we have available:**

| Field | Status | Source |
|-------|--------|--------|
| `matched_count` | ✓ EXISTS | Line 81: `sum(1 for a in assignments if a.is_matched)` |
| `mae` | ✓ EXISTS | Line 78: calculated in `_match_shifts()` |
| `tolerance` | ✓ EXISTS | Line 36: `self.tolerance` (default 3.0 ppm) |
| `is_matched` property | ✓ EXISTS | models.py line 28-30: checks `experimental_shift is not None` |

**What `is_matched` means:**

From `_match_shifts()` lines 154-156:
```python
is_within_tolerance = (
    closest_error is not None and closest_error <= self.tolerance
)
```

So `is_matched` means: "predicted shift is within tolerance (default 3 ppm) of an experimental shift".

**Current tolerance values:**

| Location | Value | Purpose |
|----------|-------|---------|
| Ranker constructor | 3.0 ppm (default) | Determines `is_matched` status |
| CLI `lucy lsd rank` | 3.0 ppm (default) | User-configurable via `--tolerance` flag |

**Sherlock uses 10 ppm for match counting**, but lucy-ng defaults to 3 ppm. We should:
- Keep existing 3 ppm default for backward compatibility
- Allow CLI override: `--match-tolerance 10.0` (separate from deviation tolerance)
- OR: Use the same tolerance for both (simpler, may be sufficient)

### 1.2 Current Data Models

**File:** `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/ranking/models.py`

**RankedSolution model (lines 33-133):**

```python
class RankedSolution(BaseModel):
    solution_index: int
    smiles: str
    mae: float
    matched_count: int          # ✓ Already exists!
    total_carbons: int
    prediction_rate: float
    assignments: list[ShiftAssignment]

    @property
    def match_rate(self) -> float:  # Lines 53-58
        """Fraction of predicted carbons matched to experimental peaks."""
        if self.total_carbons == 0:
            return 0.0
        return self.matched_count / self.total_carbons
```

**Key observation:** `matched_count` already exists and is correctly calculated. We just need to change the sort order.

**Assignments structure (lines 6-30):**

```python
class ShiftAssignment(BaseModel):
    atom_index: int
    predicted_shift: float
    experimental_shift: float | None  # Set only if within tolerance
    error: float | None               # Always set (for MAE calculation)
    closest_experimental: float | None  # Always set (for matching)

    @property
    def is_matched(self) -> bool:
        return self.experimental_shift is not None
```

**Critical insight:** The current implementation tracks BOTH:
- `error`: always set (used for MAE calculation, includes out-of-tolerance predictions)
- `experimental_shift`: only set if within tolerance (used for `is_matched` determination)

This is already the correct design for two-tier ranking!

### 1.3 CLI Integration

**File:** `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/cli/lsd.py`

**`lucy lsd rank` command (lines 141-328):**

```python
@lsd.command("rank")
@click.option("--tolerance", "-t", type=float, default=3.0)
def lsd_rank(smiles_file, spectrum, shifts, top, tolerance, table, output_format):
    # ... (lines omitted)
    ranker = SolutionRanker.from_table_file(
        table_path=str(table_path),
        tolerance=tolerance,  # Used for is_matched determination
    )
    result = ranker.rank(solutions, experimental_shifts, top_n=top)
```

**Output formats:**

| Format | Status | Lines |
|--------|--------|-------|
| JSON | ✓ DETAILED | Lines 279-305: includes mae, quality, matched_count, deviations |
| Text | ✓ SUMMARY | Lines 307-327: shows rank, MAE, quality, tolerance_summary |

**JSON output already includes `matched_count`** (line 300), so no schema changes needed for clients!

### 1.4 HOSE Radius Transparency

**RANK-05 requirement:** "Ranking reports HOSE prediction radius used per carbon"

**Status:** ✓ ALREADY IMPLEMENTED

**Evidence:**

`PredictedShift` model (prediction/models.py lines 33-47):
```python
class PredictedShift(BaseModel):
    atom_index: int
    shift: float
    confidence: float
    hose_code: str
    radius_used: int  # ← Already tracked!
    match_count: int
    std_dev: float
    min_shift: float
    max_shift: float
```

**How it works:**

The C13Predictor uses a fallback strategy (6 → 5 → 4 → ... → 1) and stores `radius_used` for each successful prediction. This is already accessible via:
- `PredictionResult.predictions[i].radius_used`
- `RankedSolution.assignments[i]` (ShiftAssignment has atom_index, can join to predictions)

**What's missing:**

The `ShiftAssignment` model doesn't include `radius_used`. We could add it for transparency:

```python
class ShiftAssignment(BaseModel):
    atom_index: int
    predicted_shift: float
    experimental_shift: float | None
    error: float | None
    closest_experimental: float | None
    radius_used: int | None = None  # NEW: Add for transparency
    confidence: float | None = None  # NEW: Add for transparency
```

But this is **optional** — the radius is already stored in the `PredictionResult` that feeds into ranking, just not propagated to `ShiftAssignment`.

---

## 2. The MAE Hallucination Problem (Ibuprofen Case Study)

### 2.1 Root Cause

From Sherlock analysis (`background/sherlock-analysis.md` lines 149-154):

> **Impact:** In case 21 (3-hydroxy-drimenol), the correct solution had 10/13 matching signals while incorrect candidates had lower deviation but fewer matches. The two-tier ranking is critical for diastereotopic carbon cases.
>
> **What lucy-ng does:** Ranks by MAE only. This contributed to the ibuprofen hallucination -- wrong cyclohexadiene solutions had MAE 1.93 ppm which appeared "Excellent" because all 13 carbons were "matched" (even though the matching was to wrong structural positions).

**The problem in detail:**

| Solution | Structure | MAE | Matched | Sort Key (current) | Sort Key (correct) |
|----------|-----------|-----|---------|-------------------|-------------------|
| Wrong | Cyclohexadiene | 1.93 ppm | 11/13 | (1.93, -11) | (-11, 1.93) |
| Correct | Ibuprofen | 2.13 ppm | 13/13 | (2.13, -13) | (-13, 2.13) |

Current sort: `(r.mae, -r.matched_count)` → Wrong solution ranks #1 (lower MAE)
Correct sort: `(-r.matched_count, r.mae)` → Correct solution ranks #1 (more matches)

**Why this happens:**

Wrong structures can have coincidentally low MAE if:
1. Some predicted shifts happen to be close to experimental shifts by chance
2. But they don't match the FULL spectrum (fewer matches)
3. MAE-only ranking rewards the coincidental closeness, ignoring incomplete coverage

**Real-world analogy:**

A student who answers 8/10 questions correctly (80%) should rank higher than a student who answers 5/10 questions correctly (50%), even if the 5 answers are slightly more accurate.

### 2.2 Sherlock's Solution

From `background/sherlock-analysis.md` lines 360-376:

> **Algorithm:**
> 1. For each LSD solution SMILES:
>    - Predict 13C shifts using HOSE-based predictor
>    - For each experimental shift, find closest predicted shift
>    - If within tolerance (default 10 ppm), count as "match"
>    - Calculate average deviation among matched signals
> 2. Sort solutions:
>    - Primary key: match_count (descending)
>    - Secondary key: average_deviation (ascending)

**Key parameters:**

| Parameter | Sherlock | lucy-ng current | Recommendation |
|-----------|----------|----------------|----------------|
| Match tolerance | 10 ppm | 3 ppm | Keep 3 ppm default, allow override |
| Deviation calc | MAE (all signals) | MAE (all signals) | No change |
| Sort order | (match_count DESC, mae ASC) | (mae ASC, match_count DESC) | **FLIP ORDER** |

### 2.3 Why 10 ppm vs 3 ppm Tolerance?

Sherlock uses 10 ppm for **match counting** but likely uses a tighter tolerance for **final ranking quality assessment**.

**Rationale:**

| Tolerance | Purpose | Strictness |
|-----------|---------|------------|
| 10 ppm (loose) | Determine if a signal "exists" in prediction | Generous — captures partial matches |
| 3 ppm (tight) | Determine quality of the match | Strict — MAE calculation uses exact errors |

**For lucy-ng:**

We should keep the single-tolerance design (3 ppm default) because:
1. It's simpler (one parameter, not two)
2. Users can override via `--tolerance` if needed
3. The key insight is **sort order**, not tolerance value
4. 3 ppm is reasonable for 13C prediction quality

If users need looser matching, they can run: `lucy lsd rank solutions.smi --shifts "..." --tolerance 10.0`

---

## 3. Badlist Patterns for Strained Rings

### 3.1 Why Badlists Matter

From Sherlock analysis (`background/sherlock-analysis.md` lines 161-167):

> **What Sherlock does:** Applies LSD's built-in 3-membered and 4-membered ring filters by default (DEFF/FEXP NOT). This prevents chemically unreasonable solutions.
>
> **What lucy-ng does:** Nothing. The agent may not think to exclude strained rings.
>
> **Implementation path:** Simple -- add the ring filter DEFF/FEXP lines to the agent's LSD template. Minimal effort.

**Impact:**

Natural products rarely contain 3- or 4-membered rings (except epoxides). Without badlist filtering:
- LSD explores unrealistic ring systems
- Solution count increases
- Runtime increases
- Agent wastes iterations on chemically implausible structures

### 3.2 LSD DEFF/FEXP NOT Syntax

**LSD commands for exclusion:**

```
; Exclude substructures using SMARTS-like syntax
DEFF NOT <pattern>   ; Define forbidden fragment
FEXP NOT <pattern>   ; Find and exclude fragment
```

**Difference between DEFF and FEXP:**

| Command | Meaning | Use Case |
|---------|---------|----------|
| DEFF | Define fragment | Faster, hardcoded patterns |
| FEXP | Find fragment | Slower, complex queries |

For simple ring patterns, use **DEFF NOT**.

### 3.3 Ring SMARTS Patterns

**3-membered rings:**

| Pattern | Structure | When to EXCLUDE | When to ALLOW |
|---------|-----------|-----------------|---------------|
| `C1CC1` | Cyclopropane | Always (unless strong evidence) | Cyclopropane derivatives (rare) |
| `C1OC1` | Epoxide | Depends on evidence | 13C shifts ~50 ppm for C-O, formula consistent |
| `C1NC1` | Aziridine | Always (very rare) | N-heterocycle with ~45 ppm shifts |
| `C1SC1` | Thiirane | Always (very rare) | Sulfur heterocycle evidence |

**4-membered rings:**

| Pattern | Structure | When to EXCLUDE | When to ALLOW |
|---------|-----------|-----------------|---------------|
| `C1CCC1` | Cyclobutane | Always (unless strong evidence) | Bridged systems (norbornane) |
| `C1OCC1` | Oxetane | Always (very rare) | Unusual O-heterocycle evidence |
| `C1NCC1` | Azetidine | Always (very rare) | N-heterocycle with ring strain |
| `C1SCC1` | Thietane | Always (very rare) | S-heterocycle evidence |

**Default badlist (apply to all CASE runs):**

```
; Exclude strained rings (natural products rarely contain these)
DEFF NOT C1CC1      ; cyclopropane
DEFF NOT C1CCC1     ; cyclobutane
DEFF NOT C1NC1      ; aziridine
DEFF NOT C1NCC1     ; azetidine
DEFF NOT C1SC1      ; thiirane
DEFF NOT C1SCC1     ; thietane
```

**Conditional badlist (agent decides based on evidence):**

```
; Only exclude epoxide if NO evidence for it
; Evidence: 13C shift ~45-55 ppm for C-O, formula has appropriate O count
DEFF NOT C1OC1      ; epoxide (conditional)

; Only exclude oxetane if NO evidence for it
DEFF NOT C1OCC1     ; oxetane (conditional)
```

### 3.4 Detection Logic for Conditional Patterns

**Epoxide detection:**

```python
def should_exclude_epoxide(shifts: list[float], formula: str) -> bool:
    """Returns True if epoxide should be excluded (no evidence)."""
    # Check for characteristic C-O shift range (45-55 ppm)
    has_epoxide_shift = any(45.0 <= s <= 55.0 for s in shifts)

    # Check if formula has oxygen
    has_oxygen = 'O' in formula

    # If both conditions met, DO NOT exclude (allow epoxide)
    if has_epoxide_shift and has_oxygen:
        return False

    # Otherwise, exclude epoxide
    return True
```

**Implementation approach:**

1. **Default (Phase 38):** Always exclude ALL strained rings (including epoxide)
2. **Future enhancement (Phase 39+):** Add conditional logic for epoxide/oxetane

This keeps Phase 38 simple — just document the patterns in agent knowledge.

### 3.5 Ring Statistics from Database

**Phase 36 added ring columns to `hose_stats` table:**

| Column | Type | Meaning |
|--------|------|---------|
| `in_3ring` | int | Count of HOSE codes where carbon is in a 3-membered ring |
| `in_4ring` | int | Count of HOSE codes where carbon is in a 4-membered ring |
| `in_aromatic` | int | Count of HOSE codes where carbon is in an aromatic ring |

**Potential use (future):**

```python
# Query: How often do 13C shifts at 50 ppm appear in 3-membered rings?
result = detector.query_ring_statistics(shift=50.0, ring_size=3)
# If result.frequency < 1%, exclude C1OC1 (epoxide unlikely)
# If result.frequency > 5%, allow C1OC1 (epoxide evidence)
```

**For Phase 38:**

We won't use these statistics yet — just document the hardcoded patterns. Phase 39+ can add data-driven badlist decisions.

### 3.6 Agent Knowledge Update

**File:** `~/.claude/agents/lucy-case-agent.md`

**Section to add/update:** "LSD File Generation" (Pitfall 6 area)

**Content:**

```markdown
### Badlist Filters (Exclude Strained Rings)

Natural products rarely contain 3- or 4-membered rings. Add these exclusions to EVERY LSD file:

```
; Exclude strained rings (add at end of LSD file, before END)
DEFF NOT C1CC1      ; cyclopropane
DEFF NOT C1CCC1     ; cyclobutane
DEFF NOT C1NC1      ; aziridine
DEFF NOT C1NCC1     ; azetidine
DEFF NOT C1SC1      ; thiirane
DEFF NOT C1SCC1     ; thietane
DEFF NOT C1OC1      ; epoxide (exclude unless strong evidence)
DEFF NOT C1OCC1     ; oxetane (exclude unless strong evidence)
```

**Exception:** If you see 13C shifts in the 45-55 ppm range AND the formula contains oxygen, consider allowing epoxides (remove the `DEFF NOT C1OC1` line). This is rare.
```

---

## 4. Implementation Plan

### 4.1 Plan 38-01: Modify SolutionRanker for Two-Tier Scoring

**Objective:** Change sort order from `(mae, -match_count)` to `(-match_count, mae)`

**Affected files:**
- `src/lucy_ng/ranking/ranker.py` (1 line change + docstring updates)
- `tests/test_ranking.py` (update test expectations)
- `src/lucy_ng/cli/lsd.py` (update CLI help text to describe new ranking)

**Changes required:**

1. **ranker.py line 95:**
   ```python
   # OLD (wrong order)
   ranked.sort(key=lambda r: (r.mae, -r.matched_count))

   # NEW (correct order)
   ranked.sort(key=lambda r: (-r.matched_count, r.mae))
   ```

2. **ranker.py docstrings:**
   - Line 14: Update docstring to say "ranks by signal match count first, then MAE"
   - Line 52: Update to say "RankingResult with solutions sorted by match count (best first), then MAE"

3. **tests/test_ranking.py:**
   - Update `test_rank_solutions` to expect match count as primary sort key
   - Add test case demonstrating ibuprofen-style hallucination is prevented

4. **cli/lsd.py line 307:**
   - Update summary text: "Solutions ranked by signal coverage (match count), then deviation (MAE)"

**Backward compatibility:**

- JSON output format unchanged (still includes `matched_count`, `mae`)
- CLI clients that parse JSON won't break
- CLI human-readable output won't break (just reordered)

**Testing strategy:**

```python
def test_two_tier_ranking_prevents_hallucination():
    """Test that solutions with more matches rank higher despite higher MAE."""
    # Wrong solution: low MAE, incomplete coverage
    wrong = make_solution(smiles="WRONG", mae=1.93, matched=11, total=13)

    # Correct solution: higher MAE, complete coverage
    correct = make_solution(smiles="CORRECT", mae=2.13, matched=13, total=13)

    result = ranker.rank([wrong, correct], experimental=[...])

    # Correct solution should rank #1 (more matches)
    assert result.solutions[0].smiles == "CORRECT"
    assert result.solutions[1].smiles == "WRONG"
```

**Estimated effort:** 1-2 days (mostly testing and documentation)

### 4.2 Plan 38-02: Add Signal Match Counting Logic with Tolerance

**Objective:** Verify that `matched_count` calculation is correct for two-tier ranking

**Status:** ✓ ALREADY CORRECT

**Evidence:**

Current `_match_shifts()` implementation (ranker.py lines 113-181):
1. For each predicted shift, finds closest experimental shift
2. Checks if error <= tolerance
3. Sets `is_matched` flag based on tolerance check
4. MAE is calculated from ALL shifts (not just matched)
5. `matched_count` is sum of `is_matched` flags

**This is exactly what we need!**

**Optional enhancement:** Add configurable match tolerance separate from deviation tolerance

```python
def __init__(
    self,
    predictor: C13Predictor,
    tolerance: float = 3.0,
    match_tolerance: float | None = None,  # NEW: separate tolerance for matching
) -> None:
    self.predictor = predictor
    self.tolerance = tolerance
    self.match_tolerance = match_tolerance or tolerance  # Default to same value
```

**Recommendation:** Skip this enhancement for Phase 38. Keep single tolerance parameter (simpler). Can add in Phase 39 if needed.

**Estimated effort:** 0 days (already implemented) or 1 day (if adding separate match_tolerance)

### 4.3 Plan 38-03: Document Badlist Patterns in Agent Knowledge

**Objective:** Add strained ring exclusion patterns to CASE agent's LSD generation knowledge

**Affected files:**
- `~/.claude/agents/lucy-case-agent.md` (agent knowledge update)
- No code changes (agent reads the knowledge, generates LSD files accordingly)

**Content to add:**

See section 3.6 above for exact markdown content.

**Location in agent file:**

Insert after the "HSQC Before HMBC" section (~line 300) and before the "Pitfalls" section.

**Testing strategy:**

1. Run CASE agent on a test compound
2. Inspect generated LSD file
3. Verify presence of `DEFF NOT` lines for all 8 strained ring patterns
4. Verify solutions do NOT contain those patterns

**Estimated effort:** 1 day (write content, test agent behavior)

### 4.4 Optional: Add HOSE Radius to ShiftAssignment

**Objective:** Propagate `radius_used` and `confidence` from predictions to assignments for transparency

**Status:** NOT REQUIRED for Phase 38 success criteria

**Why it's useful:**

- Users can see which predictions are low-confidence (high radius fallback)
- Ranking reports can highlight "this solution has 3 carbons predicted at radius 1 only"
- Debugging tool for prediction quality

**Changes required:**

1. **models.py (ShiftAssignment):**
   ```python
   class ShiftAssignment(BaseModel):
       atom_index: int
       predicted_shift: float
       experimental_shift: float | None
       error: float | None
       closest_experimental: float | None
       radius_used: int | None = None      # NEW
       confidence: float | None = None      # NEW
       hose_code: str | None = None         # NEW (optional)
   ```

2. **ranker.py (_match_shifts):**
   ```python
   assignment = ShiftAssignment(
       atom_index=pred.atom_index,
       predicted_shift=pred.shift,
       experimental_shift=closest_shift if is_within_tolerance else None,
       error=closest_error,
       closest_experimental=closest_shift,
       radius_used=pred.radius_used,       # NEW
       confidence=pred.confidence,         # NEW
       hose_code=pred.hose_code,          # NEW
   )
   ```

3. **cli/lsd.py (JSON output):**
   Add `radius_used`, `confidence` to per-assignment output

**Estimated effort:** 1 day (if included)

**Recommendation:** Defer to Phase 39. Not critical for Phase 38 success.

---

## 5. Dependencies and Blockers

### 5.1 Prerequisites

| Dependency | Status | Notes |
|------------|--------|-------|
| Phase 36 (ring statistics) | ✓ COMPLETE | Ring columns exist in hose_stats, not used until Phase 39 |
| Existing ranking infrastructure | ✓ COMPLETE | `matched_count` already calculated correctly |
| LSD DEFF/FEXP NOT support | ✓ COMPLETE | LSD binary supports these commands |
| Agent knowledge update mechanism | ✓ COMPLETE | Agent reads from ~/.claude/agents/lucy-case-agent.md |

**No blockers.** All dependencies satisfied.

### 5.2 Downstream Impact

| Affected Component | Impact | Mitigation |
|-------------------|--------|------------|
| CASE agent | Must read and use badlist patterns | Update agent knowledge file |
| Dereplication | None | Separate from CASE ranking |
| Prediction CLI | None | Only ranking sort order changed |
| JSON output schema | None | Same fields, different order |

**Low risk.** Changes are isolated to ranking module and agent knowledge.

---

## 6. Testing Strategy

### 6.1 Unit Tests

**File:** `tests/test_ranking.py`

**New tests to add:**

1. `test_two_tier_ranking_match_count_primary()`
   - Create solutions with different (matched_count, mae) pairs
   - Verify correct sort order: (-matched_count, mae)

2. `test_hallucination_prevention()`
   - Simulate ibuprofen case: wrong solution with low MAE but fewer matches
   - Verify correct solution (more matches, higher MAE) ranks #1

3. `test_equal_match_count_fallback_to_mae()`
   - Create solutions with same matched_count
   - Verify MAE is used as tiebreaker (lower MAE wins)

4. `test_backward_compat_all_matched()`
   - When all solutions have 100% match rate, ranking reduces to MAE-only
   - Verify this still works correctly

**Estimated effort:** 4-6 test cases, ~1 day

### 6.2 Integration Tests

**Ibuprofen CASE run:**

```bash
# Existing test data
cd tests/data/Ibuprofen

# Run CASE agent with new ranking
/lucy-ng:case

# Expected outcome:
# - Agent generates LSD file with badlist patterns
# - Solutions ranked by match count first
# - Correct ibuprofen structure ranks #1
# - Wrong cyclohexadiene structures (if generated) rank lower
```

**Success criteria:**

- No cyclohexadiene solutions in top 5
- Correct ibuprofen SMILES at rank #1
- MAE < 3.0 ppm for top solution
- All DEFF NOT lines present in LSD file

**Estimated effort:** 1 day (run, verify, document)

### 6.3 Regression Tests

**Existing test compounds:**

Run CASE on existing test compounds from v2.1:
- Sarocladone A (should still work)
- Any other successful CASE runs

**Verify:**

- Ranking still produces reasonable results
- No regressions in solution quality
- Agent successfully adds badlist patterns

**Estimated effort:** 1 day

---

## 7. Documentation Updates

### 7.1 User-Facing Documentation

**File:** `CLAUDE.md`

**Section:** CLI Output Reference (line ~50)

**Update `lucy lsd rank` output description:**

```markdown
| Command | Key Output Fields (JSON) |
|---------|--------------------------|
| `lucy lsd rank` | ranked_solutions (smiles, matched_count, mae, quality, deviations) |
```

Add note:
```markdown
**Ranking algorithm:** Solutions are ranked by:
1. Number of matching signals (descending) — ensures complete spectral coverage
2. Mean Absolute Error (ascending) — among solutions with equal match count

This prevents wrong solutions with coincidentally low MAE from outranking correct solutions with incomplete spectral matches.
```

### 7.2 Agent Knowledge Updates

**File:** `~/.claude/agents/lucy-case-agent.md`

**Updates:**

1. **Add Badlist section** (see 3.6 above)
2. **Update Ranking interpretation:**
   ```markdown
   When ranking LSD solutions, `lucy lsd rank` now prioritizes:
   1. Match count (how many experimental signals are matched)
   2. MAE (deviation among matched signals)

   Always report BOTH metrics. A solution with 13/13 matches and MAE 2.5 is BETTER than 11/13 matches and MAE 1.8 (incomplete coverage).
   ```

### 7.3 Planning Documentation

**Files to update:**

- `ROADMAP.md`: Mark Phase 38 as complete
- `STATE.md`: Update current position to Phase 39
- `REQUIREMENTS.md`: Mark RANK-01 through RANK-04 as satisfied

---

## 8. Success Criteria Validation

### 8.1 RANK-01: Two-tier ranking implemented

**Observable truth:**

```python
# src/lucy_ng/ranking/ranker.py line 95
ranked.sort(key=lambda r: (-r.matched_count, r.mae))
```

**Test:**

```python
def test_rank_01_two_tier_scoring():
    sol1 = RankedSolution(matched_count=13, mae=2.5)
    sol2 = RankedSolution(matched_count=11, mae=1.8)

    # After sorting: sol1 (13 matches) should rank #1
    assert ranked[0].matched_count > ranked[1].matched_count
```

### 8.2 RANK-02: Fewer matches rank lower

**Observable truth:**

A solution with 11/13 matched signals CANNOT rank above a solution with 13/13 matched signals, regardless of MAE.

**Test:**

```python
def test_rank_02_incomplete_coverage_penalty():
    incomplete = RankedSolution(matched_count=10, mae=0.5)  # Amazing MAE
    complete = RankedSolution(matched_count=13, mae=5.0)    # Poor MAE

    # After sorting: complete ranks #1 (more matches)
    assert ranked[0].matched_count == 13
```

### 8.3 RANK-03: 3-ring badlist

**Observable truth:**

```bash
# Agent-generated LSD file contains:
DEFF NOT C1CC1   # cyclopropane
DEFF NOT C1OC1   # epoxide
DEFF NOT C1NC1   # aziridine
DEFF NOT C1SC1   # thiirane
```

**Test:** Manual inspection of agent-generated LSD files

### 8.4 RANK-04: 4-ring badlist

**Observable truth:**

```bash
# Agent-generated LSD file contains:
DEFF NOT C1CCC1   # cyclobutane
DEFF NOT C1OCC1   # oxetane
DEFF NOT C1NCC1   # azetidine
DEFF NOT C1SCC1   # thietane
```

**Test:** Manual inspection of agent-generated LSD files

### 8.5 RANK-05: HOSE radius transparency

**Observable truth:**

```python
# PredictedShift already has radius_used field
pred = predictor.predict_from_smiles("CCO")
assert pred.predictions[0].radius_used in range(1, 7)
```

**Status:** ✓ Already satisfied (no changes needed)

---

## 9. Risk Assessment

### 9.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Sort order change breaks existing workflows | Low | Medium | Comprehensive testing, JSON schema unchanged |
| Badlist patterns too strict (exclude valid structures) | Low | Medium | Document exception cases (epoxide), agent can remove patterns |
| Tolerance value mismatch (3 ppm vs 10 ppm) | Medium | Low | Keep 3 ppm default, document in CLI help |
| Agent doesn't consistently add badlist patterns | Medium | Low | Add to agent knowledge prominently, test on multiple compounds |

### 9.2 User Impact

| Impact | Severity | Users Affected |
|--------|----------|---------------|
| Ranking order changes | Medium | All lucy lsd rank users |
| Solution ranks may shift | Low | CASE workflows only |
| Badlist may exclude valid rare structures | Low | Edge cases only (epoxides, bridged rings) |

**Mitigation:**

- Clear documentation of ranking change
- CLI help text explains new algorithm
- Agent can override badlist for exceptional cases

### 9.3 Rollback Plan

If Phase 38 causes issues:

1. Revert ranker.py line 95 to old sort order
2. Remove badlist patterns from agent knowledge
3. Regression tests should still pass

**Rollback complexity:** Very low (1-line change + doc update)

---

## 10. Effort Estimation

### 10.1 Development Tasks

| Task | Effort | Assignee |
|------|--------|----------|
| 38-01: Modify ranker sort order | 1-2 days | Claude (gsd-executor) |
| 38-02: Verify match counting (already done) | 0 days | N/A |
| 38-03: Document badlist patterns | 1 day | Claude (gsd-executor) |
| Integration testing | 1-2 days | Claude (gsd-executor) |
| Documentation updates | 1 day | Claude (gsd-executor) |

**Total estimated effort:** 4-6 days

### 10.2 Critical Path

```
38-01 (ranker modification) → Integration testing → Documentation
     ↓
38-03 (badlist docs) ----→ Agent testing --------→ Documentation
```

**Parallel work possible:**

- 38-01 and 38-03 can be developed simultaneously
- Integration testing requires both complete

**Expected duration:** 1 week (5-7 working days)

---

## 11. Open Questions

### Q1: Should we add separate match_tolerance parameter?

**Options:**

A. Keep single `tolerance` parameter (simpler)
B. Add `match_tolerance` separate from `deviation_tolerance`

**Recommendation:** Option A for Phase 38. Defer B to Phase 39 if users request it.

**Rationale:** Sherlock uses 10 ppm for matching, but lucy-ng's 3 ppm default is reasonable for 13C. Users can override with `--tolerance 10.0` if needed.

### Q2: Should badlist patterns be hardcoded or data-driven?

**Options:**

A. Hardcoded patterns in agent knowledge (Phase 38)
B. Data-driven from ring statistics (Phase 39+)

**Recommendation:** Option A for Phase 38. Option B for Phase 40 (statistical badlist).

**Rationale:** Phase 36 added ring statistics infrastructure, but we don't have enough data yet to set frequency thresholds. Hardcoded patterns are sufficient for v3.0.

### Q3: Should we propagate radius_used to ShiftAssignment?

**Options:**

A. Skip for Phase 38 (not required for success criteria)
B. Add for transparency (1 day extra effort)

**Recommendation:** Option A for Phase 38. Defer to Phase 39 if demand exists.

**Rationale:** RANK-05 is satisfied by PredictedShift.radius_used existing. Adding to ShiftAssignment is nice-to-have, not critical.

### Q4: How to handle epoxide exception?

**Options:**

A. Always exclude epoxides (Phase 38)
B. Conditional exclusion based on shift evidence (Phase 39)

**Recommendation:** Option A for Phase 38. Document exception case in agent knowledge. Agent can manually remove `DEFF NOT C1OC1` line if strong evidence exists.

**Rationale:** Keeps Phase 38 simple. Most natural products don't have epoxides. When they do, the shift evidence is usually clear (~50 ppm for C-O).

---

## 12. Implementation Checklist

### Phase 38 Must-Haves

- [ ] ranker.py line 95: Change sort to `(-matched_count, mae)`
- [ ] ranker.py docstrings: Update to reflect two-tier ranking
- [ ] tests/test_ranking.py: Add hallucination prevention test
- [ ] tests/test_ranking.py: Add two-tier sort order test
- [ ] cli/lsd.py: Update help text to describe new ranking
- [ ] lucy-case-agent.md: Add badlist patterns section
- [ ] lucy-case-agent.md: Update ranking interpretation guidance
- [ ] CLAUDE.md: Update CLI output reference
- [ ] Integration test: Ibuprofen CASE run with new ranking
- [ ] Regression test: Existing test compounds still work

### Phase 38 Nice-to-Haves (Defer to 39+)

- [ ] Add `match_tolerance` separate from `tolerance`
- [ ] Propagate `radius_used` to ShiftAssignment
- [ ] Data-driven badlist from ring statistics
- [ ] Conditional epoxide exclusion logic

---

## 13. References

### Primary Sources

| Source | Location | Relevance |
|--------|----------|-----------|
| Sherlock analysis | background/sherlock-analysis.md | Two-tier ranking algorithm, badlist patterns |
| Feature research | .planning/research/FEATURES.md | Detailed specifications for ranking |
| Phase 36 verification | .planning/phases/36-hhb-and-ring-detection/36-VERIFICATION.md | Ring statistics infrastructure |

### Code References

| File | Lines | Content |
|------|-------|---------|
| src/lucy_ng/ranking/ranker.py | 95 | Current sort order (needs change) |
| src/lucy_ng/ranking/models.py | 33-133 | RankedSolution model (already has matched_count) |
| src/lucy_ng/prediction/models.py | 33-47 | PredictedShift model (has radius_used) |
| src/lucy_ng/cli/lsd.py | 141-328 | CLI command (help text needs update) |

### Test References

| File | Lines | Coverage |
|------|-------|----------|
| tests/test_ranking.py | 228-441 | Existing ranking tests (need updates) |

---

## 14. Confidence Assessment

| Area | Confidence | Justification |
|------|------------|---------------|
| Two-tier ranking algorithm | HIGH | Directly from Sherlock thesis, confirmed by ibuprofen case study |
| Existing code readiness | HIGH | matched_count already calculated correctly, 1-line change needed |
| Badlist patterns | HIGH | Standard DEFF NOT syntax, documented in LSD manual |
| HOSE radius transparency | HIGH | Already implemented, no changes needed |
| Testing strategy | HIGH | Clear success criteria, ibuprofen provides perfect test case |
| Effort estimate | MEDIUM | Small code changes, but integration testing may reveal issues |
| Risk level | LOW | Changes are isolated, rollback is trivial |

**Overall confidence:** HIGH — This is a low-risk, high-impact phase with clear requirements and minimal implementation complexity.

---

## 15. Summary: What You Need to Know to Plan Well

### Key Insights

1. **The fix is simpler than expected:** Existing code already calculates `matched_count` correctly. Just flip the sort order (1-line change).

2. **The problem is well-understood:** Ibuprofen hallucination is a perfect test case. We know exactly what went wrong and how to fix it.

3. **Badlist is documentation, not code:** Agent knowledge update only. No new CLI commands or database queries.

4. **HOSE radius is already done:** PredictedShift.radius_used exists. No implementation needed.

5. **Testing is straightforward:** Unit tests verify sort order. Integration test runs ibuprofen CASE and checks rank #1.

### Critical Decisions

| Decision | Recommendation | Rationale |
|----------|----------------|-----------|
| Sort order | `(-matched_count, mae)` | Matches Sherlock algorithm |
| Tolerance | Keep 3 ppm default | Simpler, users can override |
| Badlist | Hardcoded patterns | Sufficient for v3.0, defer data-driven to v3.1 |
| HOSE radius | No changes needed | Already implemented |
| Effort | 4-6 days | Small code changes, comprehensive testing |

### Plan Structure

**38-01-PLAN.md:** Modify SolutionRanker for two-tier scoring
- Change sort order (1 line)
- Update docstrings (3 locations)
- Add unit tests (4 test cases)
- Update CLI help text (1 location)

**38-02-PLAN.md:** Signal match counting logic verification
- Verify existing implementation is correct
- Document algorithm in code comments
- No code changes required

**38-03-PLAN.md:** Document badlist patterns
- Update lucy-case-agent.md (1 new section)
- Add DEFF NOT patterns (8 lines)
- Document exception cases (epoxide)
- Test agent behavior on sample compound

### Success Metrics

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Sort order | `(-matched_count, mae)` | Code inspection |
| Ibuprofen rank | Correct structure at #1 | Integration test |
| Badlist in LSD files | All 8 patterns present | Manual inspection |
| Test pass rate | 100% | pytest |
| Regression | No failures | Existing test compounds |

**Phase 38 is ready to plan.**

---

_Researched: 2026-02-11_
_Researcher: Claude (gsd-phase-researcher)_
_Confidence: HIGH_
