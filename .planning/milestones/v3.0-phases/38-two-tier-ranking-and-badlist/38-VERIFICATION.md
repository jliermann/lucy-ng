---
phase: 38-two-tier-ranking-and-badlist
verified: 2026-02-11T16:45:00Z
status: passed
score: 11/11 must-haves verified
---

# Phase 38: Two-Tier Ranking and Badlist Verification Report

**Phase Goal:** Implement two-tier ranking (match count first, then MAE) and badlist filters for strained ring exclusion

**Verified:** 2026-02-11T16:45:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Solutions with more matched signals rank higher regardless of MAE | ✓ VERIFIED | Sort key `(-r.matched_count, r.mae)` in ranker.py:95, test_hallucination_prevention passes with CORRECT (13/13, MAE=1.71) ranking above WRONG (11/13, MAE=0.72) |
| 2 | Solutions with equal match count fall back to MAE for tiebreaking | ✓ VERIFIED | test_equal_match_count_fallback_to_mae passes, both solutions 5/5 matched, BETTER_MAE ranks #1 |
| 3 | When all solutions have 100% match rate, ranking reduces to MAE-only (backward compat) | ✓ VERIFIED | test_backward_compat_all_matched passes, all solutions 3/3 matched, ordered by MAE ascending |
| 4 | RankingResult docstrings describe two-tier ranking (match count first, then MAE) | ✓ VERIFIED | models.py:147 "sorted by match count (best first), then MAE", ranker.py:52 "sorted by match count (best first), then MAE" |
| 5 | CLI text output shows match count per solution | ✓ VERIFIED | cli/lsd.py:320 "Matched={sol.matched_count}/{sol.total_carbons}" |
| 6 | ShiftAssignment carries radius_used from PredictedShift for HOSE radius transparency | ✓ VERIFIED | models.py:26-28 radius_used field exists, ranker.py:170 propagates pred.radius_used |
| 7 | CLI JSON output includes radius_used per assignment | ✓ VERIFIED | Pydantic auto-serialization includes all fields, manual test confirms radius_used=4 serialized |
| 8 | CASE agent knowledge contains 8 DEFF NOT patterns for strained ring exclusion | ✓ VERIFIED | grep count returns 10 (8 patterns + 2 in context text), all 8 patterns present: C1CC1, C1CCC1, C1NC1, C1NCC1, C1SC1, C1SCC1, C1OC1, C1OCC1 |
| 9 | Agent knowledge explains exception case for epoxides | ✓ VERIFIED | "Exception: If 13C spectrum shows shifts in 45-55 ppm range AND formula contains oxygen..." documented with removal guidance |
| 10 | CLAUDE.md documents two-tier ranking algorithm | ✓ VERIFIED | "Ranking algorithm: Solutions ranked by signal match count (descending), then MAE (ascending)" + matched_count in CLI Output Reference |
| 11 | Agent knowledge explains two-tier ranking interpretation | ✓ VERIFIED | "Ranking Algorithm (Two-Tier)" section: "Match count (descending)...MAE (ascending)...13/13 matched MAE 2.5 BETTER than 11/13 matches MAE 1.8" |

**Score:** 11/11 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/lucy_ng/ranking/ranker.py` | Two-tier sort: (-matched_count, mae) | ✓ VERIFIED | Line 95: `ranked.sort(key=lambda r: (-r.matched_count, r.mae))` |
| `tests/test_ranking.py` | Hallucination prevention test | ✓ VERIFIED | TestTwoTierRanking class with 4 tests, test_hallucination_prevention_ibuprofen_style passes |
| `src/lucy_ng/cli/lsd.py` | CLI output with match count | ✓ VERIFIED | Line 320: "Matched={sol.matched_count}/{sol.total_carbons}" |
| `src/lucy_ng/ranking/models.py` | ShiftAssignment with radius_used field | ✓ VERIFIED | Lines 26-28: radius_used and confidence fields, both int|None and float|None |
| `~/.claude/agents/lucy-case-agent.md` | Badlist filter patterns | ✓ VERIFIED | Contains all 8 DEFF NOT patterns with comments |
| `~/.claude/agents/lucy-case-agent.md` | Ranking interpretation guidance | ✓ VERIFIED | "Ranking Algorithm (Two-Tier)" section with match count priority explanation |
| `CLAUDE.md` | Updated ranking algorithm description | ✓ VERIFIED | Ranking algorithm note + matched_count in CLI Output Reference table |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| ranker.py | tests/test_ranking.py | sort key tested by hallucination prevention test | ✓ WIRED | Test verifies CORRECT (13/13, higher MAE) ranks above WRONG (11/13, lower MAE), proving match count is primary sort key |
| ranker.py | models.py | radius_used propagated from PredictedShift to ShiftAssignment | ✓ WIRED | ranker.py:170 assigns `radius_used=pred.radius_used`, pred is typed PredictedShift which has radius_used field |
| lucy-case-agent.md | LSD file generation | agent reads knowledge and adds DEFF NOT lines | ✓ WIRED | 8 DEFF NOT patterns in "Badlist Filters" section, referenced in checklist item 8 for LSD file construction |

### Requirements Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| RANK-01: Two-tier ranking scores by match count first, then MAE | ✓ SATISFIED | Sort key implemented, 4 tests pass including hallucination scenario |
| RANK-02: Solutions with fewer matched signals rank lower regardless of MAE | ✓ SATISFIED | test_hallucination_prevention proves this: 11/13 (MAE=0.72) ranks below 13/13 (MAE=1.71) |
| RANK-03: Badlist excludes 3-membered rings | ✓ SATISFIED | 4 patterns for 3-membered rings: C1CC1, C1NC1, C1SC1, C1OC1 |
| RANK-04: Badlist excludes 4-membered rings | ✓ SATISFIED | 4 patterns for 4-membered rings: C1CCC1, C1NCC1, C1SCC1, C1OCC1 |
| RANK-05: Ranking reports HOSE radius per carbon | ✓ SATISFIED | ShiftAssignment.radius_used field propagated from PredictedShift |

### Anti-Patterns Found

None. All files substantive with real implementations.

### Human Verification Required

None. All truths can be verified programmatically through tests and code inspection.

---

## Detailed Verification

### Plan 38-01: Two-Tier Ranking Implementation

**All 7 truths VERIFIED:**

1. **Sort order is match count primary**: `ranked.sort(key=lambda r: (-r.matched_count, r.mae))` in ranker.py:95
   - Negative sign on matched_count sorts descending (more matches = better)
   - MAE sorts ascending (lower error = better)

2. **Hallucination prevention test passes**: test_hallucination_prevention_ibuprofen_style simulates the exact failure:
   - WRONG: 11/13 matched, MAE=0.72 (ghost carbons in gaps between real signals)
   - CORRECT: 13/13 matched, MAE=1.71 (larger errors but complete coverage)
   - CORRECT ranks #1 despite higher MAE

3. **MAE tiebreaker works**: test_equal_match_count_fallback_to_mae verifies both solutions 5/5 matched, BETTER_MAE ranks #1

4. **Backward compatibility**: test_backward_compat_all_matched verifies all solutions 3/3 matched, ordered by MAE only (same as old behavior)

5. **Docstrings updated**: 
   - ranker.py:14 class docstring describes two-tier ranking
   - ranker.py:52 rank() method docstring updated
   - models.py:147 RankingResult docstring updated
   - models.py:153 solutions field description updated

6. **CLI output shows match count**: cli/lsd.py:320 displays "Matched=13/13 MAE=2.13 ppm (Good)"

7. **radius_used and confidence propagated**:
   - ShiftAssignment model extended with both fields (models.py:26-32)
   - ranker._match_shifts() passes pred.radius_used and pred.confidence (ranker.py:170-171)
   - JSON serialization automatic via Pydantic

**Artifact verification:**
- ranker.py: 208 lines, contains sort key + radius propagation + docstring updates
- models.py: 195 lines, ShiftAssignment extended, RankingResult docstring updated
- cli/lsd.py: Modified to show "Matched=N/M" in text output
- tests/test_ranking.py: TestTwoTierRanking class with 4 comprehensive tests

**Key link verification:**
- Sort key tested: test_hallucination_prevention proves match count is primary criterion
- radius_used flows: PredictedShift.radius_used → ranker._match_shifts() → ShiftAssignment.radius_used → JSON output

### Plan 38-02: Badlist Documentation

**All 4 truths VERIFIED:**

1. **8 DEFF NOT patterns present**: grep count returns 10 (8 actual patterns + 2 mentions in exception text)
   - 3-membered: C1CC1, C1NC1, C1SC1, C1OC1
   - 4-membered: C1CCC1, C1NCC1, C1SCC1, C1OCC1

2. **Epoxide exception documented**: "Exception: If 13C spectrum shows shifts in 45-55 ppm range AND molecular formula contains oxygen, remove DEFF NOT C1OC1"
   - Specific criteria: shift range + formula requirement
   - Clear action: remove the line

3. **CLAUDE.md ranking algorithm documented**:
   - CLI Output Reference table includes matched_count
   - Ranking algorithm note: "ranked by signal match count (descending), then MAE (ascending)"

4. **Agent ranking interpretation present**: "Ranking Algorithm (Two-Tier)" section explains:
   - Match count descending
   - MAE ascending
   - Example: 13/13 MAE 2.5 BETTER than 11/13 MAE 1.8
   - "Always report BOTH metrics"

**Artifact verification:**
- lucy-case-agent.md: "Badlist Filters (Exclude Strained Rings)" section added
- Manual File Construction Checklist: Item 8 added for badlist
- CLAUDE.md: matched_count in CLI output reference, ranking algorithm note added

**Key link verification:**
- Badlist section is placed in agent knowledge where LSD file generation workflow reads it
- Checklist item 8 references the badlist section, ensuring agent follows the pattern

---

## Test Results

```
$ pytest tests/test_ranking.py::TestTwoTierRanking -v
============================== test session starts ===============================
collected 4 items

tests/test_ranking.py::TestTwoTierRanking::test_two_tier_ranking_match_count_primary PASSED [ 25%]
tests/test_ranking.py::TestTwoTierRanking::test_hallucination_prevention_ibuprofen_style PASSED [ 50%]
tests/test_ranking.py::TestTwoTierRanking::test_equal_match_count_fallback_to_mae PASSED [ 75%]
tests/test_ranking.py::TestTwoTierRanking::test_backward_compat_all_matched PASSED [100%]

============================== 4 passed ==========================
```

All tests pass. Hallucination prevention test proves the core fix: solutions with more matched signals rank higher even when MAE is higher.

---

## Verification Commands

```bash
# Sort key verification
grep "ranked.sort" src/lucy_ng/ranking/ranker.py
# Output: ranked.sort(key=lambda r: (-r.matched_count, r.mae))

# radius_used propagation
grep -A 3 "radius_used=pred" src/lucy_ng/ranking/ranker.py
# Output: radius_used=pred.radius_used, confidence=pred.confidence

# ShiftAssignment fields
python -c "from lucy_ng.ranking.models import ShiftAssignment; a = ShiftAssignment(atom_index=0, predicted_shift=100.0, radius_used=4, confidence=0.9); print(f'radius_used={a.radius_used}')"
# Output: radius_used=4

# Badlist patterns count
grep -c "DEFF NOT" ~/.claude/agents/lucy-case-agent.md
# Output: 10 (8 patterns + 2 in exception text)

# CLAUDE.md ranking documentation
grep "match count" CLAUDE.md
# Output: Solutions ranked by signal match count (descending), then MAE (ascending)

# All tests pass
pytest tests/test_ranking.py::TestTwoTierRanking -v
# Result: 4/4 passed
```

---

_Verified: 2026-02-11T16:45:00Z_
_Verifier: Claude (gsd-verifier)_
