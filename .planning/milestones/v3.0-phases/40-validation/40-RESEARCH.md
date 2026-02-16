# Phase 40: Validation - Research

**Researched:** 2026-02-11
**Domain:** CASE system validation, statistical detection validation, test infrastructure
**Confidence:** HIGH

## Summary

Phase 40 validation faces a critical prerequisite blocker: the HOSE database (2.8 GB, 7.9M entries) is at schema version 3, but v3.0 statistical detection requires schema v6 with populated hybridisation, neighbour, and ring columns. All detection queries currently return "No database data" because these columns exist (via ALTER TABLE migrations) but contain only zeros.

The original roadmap envisioned validating against Sherlock's 45 test cases from nmrXiv, but this is impractical given:
1. Database regeneration is a **prerequisite blocker** (estimated 2-3 hours for full pass)
2. Each CASE run takes 5-15 minutes of agent time (45 cases = 4-11 hours)
3. We already have 2 test compounds with analysis: Ibuprofen (CASE1, v2.1 success) and Pulegone (CASE3, v3.0 partial success)

**Primary recommendation:** Validation should have two tiers: (1) unit-level CLI validation of detection commands against known structures (fast, no agent, no database regen needed for structure testing), and (2) selective full CASE validation on 3-5 representative compounds after database regeneration.

## Test Data Inventory

### Existing Test Cases

Located in `/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/`:

| Case | Compound | Formula | Status | Notes |
|------|----------|---------|--------|-------|
| CASE1 | Ibuprofen | C13H18O2 | v2.1 success | Rank #1, MAE=2.13 ppm, agent test complete |
| CASE2 | Unknown | Unknown | Unexplored | 6 experiments, no analysis dir |
| CASE3 | Pulegone | C10H16O | v3.0 tested today | Wrong keto position, detection returned no data |
| CASE4 | Unknown | Unknown | Unexplored | 7 experiments, has analysis dir |
| CASE5 | Unknown | Unknown | Partially explored | Multiple scripts, full_solutions.smi exists |
| CASE6 | Unknown | Unknown | Manual tests | 24 experiments, multiple LSD versions |
| CASE7 | Unknown | Unknown | Failed case | Marked as -failed, multiple solution files |
| CASE7-failed | Unknown | Unknown | Archive | Duplicate of CASE7 |
| CASE8 | Unknown | Unknown | Unexplored | 8 experiments, has analysis dir |

**Key findings from CASE3 (Pulegone) test (2026-02-11):**
- Database blocker confirmed: ALL statistical detection queries returned "No database data"
- Agent doesn't use COSY: identified COSY data but never used it for H-H connectivity
- Structure almost correct: CC(C)=C1CCC(C)C(=O)C1 vs correct CC(C)=C1CCC(C)CC1=O (keto group position)
- 13C prediction rated "Poor": MAE=5.37 ppm, only 3/10 shifts within 3 ppm
- Agent dismissed poor prediction as "HOSE database limitations" rather than questioning structure

**Ibuprofen (CASE1) known issue:**
- v2.1 agent produced cyclohexadiene solutions (rank #1 but wrong structure)
- Root cause: 4-bond HMBC + rigid assignment + no statistical constraints
- This is the test case that motivated v3.0 statistical detection

### Pytest Test Infrastructure

**Test suite size:** 732 test functions across 42 files
**Coverage:** All v3.0 detection modules have unit tests

Existing test files relevant to validation:
- `test_detection_hybridisation.py` (13 tests)
- `test_detection_neighbours.py` (17 tests)
- `test_signal_grouping.py` (21 tests)
- `test_ranking.py` (28 tests)
- `test_prediction.py` (46 tests)
- `test_lsd_integration.py` (8 tests)

**Current limitation:** Detection tests use synthetic data with hardcoded HOSE entries, not the full database. This validates logic but not real-world accuracy.

## Database Regeneration Blocker

### Current State

```
Database: data/reference/lucy-ng-derep.db
Size: 2.8 GB
Schema version: 3 (PRAGMA user_version = 0, but code reports v6)
HOSE entries: 7,890,374
Current columns: hose_code, radius, mean, std, count, m2 (6 columns only)
Missing columns: sp3_count, sp2_count, sp1_count, has_*_neighbor (8 columns), in_*ring (3 columns)
```

**Schema migration history:**
- v3: Original HOSE stats (6 columns)
- v4: Added hybridisation columns (sp3_count, sp2_count, sp1_count) via ALTER TABLE
- v5: Added neighbour columns (has_carbon_neighbor, has_oxygen_neighbor, etc.) via ALTER TABLE
- v6: Added ring columns (in_3ring, in_4ring, in_aromatic) via ALTER TABLE

**Problem:** ALTER TABLE adds columns with DEFAULT 0, but doesn't populate them. The database has the schema structure but zero data in detection columns.

### Regeneration Process

**Command:**
```bash
lucy database generate-hose-stats --sdf data/reference/predicted_coconut.sdf
```

**Input:** predicted_coconut.sdf (4.4 GB, 173M lines)
**Output:** Replaces all hose_stats entries with v6 schema fully populated
**Estimated time:** 2-3 hours (from Phase 34-03 notes)
**Memory:** O(1) per HOSE code via Welford's algorithm
**Resumability:** Checkpoint-based, can resume after interruption

**Features:**
- Processes in 10K compound chunks (configurable)
- File-based logging for detached operation (nohup)
- Fresh start option (--fresh clears existing data)

**Implications for Phase 40:**
- Regeneration MUST complete before meaningful detection validation
- This is a one-time blocker, not part of the validation workflow
- Cannot validate detection accuracy without populated database

## Validation Scope Options

### Option A: Full Sherlock-Style Validation (Impractical)

**Original roadmap vision:**
- Download 45 test cases from nmrXiv (Sherlock's validation set)
- Sanitize each dataset (remove compound identifiers)
- Run full CASE workflow on each (5-15 min per compound)
- Compute metrics: constraint accuracy, search space reduction, rank improvement

**Time estimate:**
- Download/sanitization: ~2-3 hours (manual)
- Database regeneration: 2-3 hours (prerequisite)
- 45 CASE runs: 4-11 hours (agent time)
- Analysis/reporting: 2-3 hours
- **Total: 10-20 hours**

**Problem:** Unrealistic for a single phase, and premature given the database blocker.

### Option B: Two-Tier Validation (Recommended)

**Tier 1: Unit-Level CLI Validation (No Database Regen Required)**

Validate detection CLI commands against known structures WITHOUT running full CASE:

1. **Hybridisation detection accuracy:**
   - Test: `lucy detect hybridisation 130.5` on known aromatics
   - Verify: sp2 frequency dominates
   - Method: Use existing test database or synthetic entries

2. **Neighbour detection accuracy:**
   - Test: `lucy detect neighbours 180.5 --hybridisation sp2` on known carbonyls
   - Verify: O mandatory, C common
   - Method: Synthetic HOSE entries with known contexts

3. **Signal grouping correctness:**
   - Test: `lucy detect grouping --shifts "44.90,45.03,129.38"` (ibuprofen case)
   - Verify: Groups {44.90, 45.03} detected at 0.25 ppm tolerance
   - Method: Pure algorithm test, no database

4. **Two-tier ranking correctness:**
   - Test: Rank solutions with (a) high MAE on all signals vs (b) low MAE on subset
   - Verify: Solution (a) ranks higher (complete coverage beats partial fit)
   - Method: Synthetic prediction results

5. **Badlist filtering:**
   - Test: Solutions with 3/4-membered non-epoxide rings flagged
   - Verify: Correct DEFF NOT patterns applied
   - Method: Known problematic SMILES

**Time estimate:** 2-3 hours (write test cases, run, document)
**Blocker status:** NOT blocked by database regeneration (uses synthetic data)

**Tier 2: Selective Full CASE Validation (After Database Regen)**

Run full CASE workflow on 3-5 representative compounds:

1. **Ibuprofen (C13H18O2)** - v2.1 failure case, must fix with v3.0
   - Expected: Correct isobutylphenylpropanoic acid structure in top 3
   - Validates: Signal grouping (44.90/45.03 ppm), aromatic detection

2. **Pulegone (C10H16O)** - v3.0 test case with wrong keto position
   - Expected: Correct CC(C)=C1CCC(C)CC1=O structure
   - Validates: Ketone hybridisation, COSY usage fix

3. **Simple test (C6-C8)** - Fast sanity check
   - Expected: Rank #1 correct structure, low MAE
   - Validates: Basic detection pipeline works

4. **Complex test (C15-C20)** - Stress test (optional)
   - Expected: Solution space dramatically reduced vs v2.1
   - Validates: Detection impact on larger molecules

**Time estimate:** 2-4 hours (after database regen: 3 runs × 15 min + analysis)
**Blocker status:** BLOCKED until database regeneration complete

### Option C: Database-First Validation (Alternative)

1. Regenerate database (2-3 hours, run overnight)
2. Validate detection queries against database (1-2 hours)
3. Run 3 CASE tests (1-2 hours)
4. Write validation report (1 hour)

**Total: 5-8 hours, but frontloaded with database work**

## Metrics for Validation

### Detection Accuracy Metrics

| Metric | What It Measures | How to Compute |
|--------|------------------|----------------|
| **Hybridisation precision** | % of sp2 predictions that are truly sp2 | Manual verification on known compounds |
| **Neighbour constraint accuracy** | % of mandatory neighbours that are correct | Compare detection vs known structures |
| **False positive rate** | % of forbidden elements incorrectly excluded | Test edge cases (e.g., rare heteroatoms) |
| **Grouping tolerance correctness** | Signals <0.25 ppm grouped, >0.25 ppm separate | Algorithm test with synthetic shifts |

### CASE Workflow Metrics

| Metric | What It Measures | v2.1 Baseline | v3.0 Target |
|--------|------------------|---------------|-------------|
| **Solution count** | LSD solutions before ranking | 100s-1000s | <100 (detection constrains) |
| **Correct rank** | Position of correct structure | Variable | Top 3 |
| **Prediction MAE** | 13C shift prediction error | 2-5 ppm | <3 ppm (correct structure) |
| **Iterations to solve** | Agent LSD refinement cycles | 5-10 | 1-3 (fewer with constraints) |

### Regression Metrics

Must not break existing functionality:

| Test | Passes |
|------|--------|
| Unit tests (pytest) | 732/732 |
| Dereplication (CASE1) | Formula match found |
| Peak picking (DEPT-guided) | All DEPT carbons found |
| LSD integration | Solutions generated |

## Common Pitfalls

### Pitfall 1: Database Version Confusion

**What goes wrong:** Tests pass with synthetic data but fail with real database because schema version mismatch.

**Why it happens:** ALTER TABLE migrations add columns but don't populate them. Code checks for column existence, not data presence.

**How to avoid:**
- Add database version check to detection CLI commands
- Warn if schema v6 detected but columns are all zeros
- Document regeneration as prerequisite in validation report

**Warning signs:**
- Detection queries return empty results on real database
- Synthetic tests pass but CASE tests fail
- User confusion about "database exists but no data"

### Pitfall 2: Overfitting to Ibuprofen

**What goes wrong:** Validation focuses only on ibuprofen case, missing edge cases that break other compounds.

**Why it happens:** Ibuprofen motivated v3.0, so it's the obvious test case.

**How to avoid:**
- Include diversity: small (C6-C8), medium (C10-C15), large (C20+)
- Include different functional groups: ketones, esters, aromatics, amides
- Include edge cases: high symmetry, multiple close signals, heteroatoms

**Warning signs:**
- Validation report only mentions ibuprofen
- No test failures despite major code changes
- User reports failures on compounds unlike ibuprofen

### Pitfall 3: Agent Autonomy vs Test Determinism

**What goes wrong:** Agent makes different decisions on repeated runs, making metrics unreproducible.

**Why it happens:** AI agents are non-deterministic, especially with complex reasoning.

**How to avoid:**
- Run each test case 2-3 times, report range
- Focus on must-pass criteria (correct structure in top 3) not exact rank
- Use temperature=0 or fixed seeds if available
- Document agent version (claude-opus-4-6)

**Warning signs:**
- Rank #1 on first run, rank #5 on second run
- Validation metrics change each time
- User complains "worked yesterday, failed today"

### Pitfall 4: Premature Validation Without Database

**What goes wrong:** Validation phase marked complete but detection never tested on real data.

**Why it happens:** Database regeneration blocker deferred, validation proceeds with synthetic data only.

**How to avoid:**
- Split validation into Tier 1 (synthetic) and Tier 2 (real database)
- Mark Phase 40 as "partially complete" until database regen + Tier 2
- Document regeneration as post-phase action item

**Warning signs:**
- Validation report mentions "future work" for real database testing
- No CASE runs included in validation
- Detection CLI commands not tested end-to-end

## Code Examples

### Unit-Level Detection Validation

```python
# tests/test_detection_validation.py

def test_hybridisation_detection_aromatic_carbons():
    """Validate sp2 dominates for known aromatic shifts."""
    detector = StatisticalDetector(db_path)

    # Known aromatic carbon shift (e.g., benzene at 128 ppm)
    result = detector.detect_hybridisation(
        shift_ppm=128.0,
        radius=3,
        window_ppm=2.0,
        min_frequency=0.01
    )

    assert result.has_data
    assert result.distributions["sp2"] > 0.90  # >90% sp2
    assert result.distributions["sp3"] < 0.05  # <5% sp3
    assert "sp2" in result.allowed_states
    assert "sp3" not in result.allowed_states

def test_signal_grouping_close_shifts():
    """Validate grouping for shifts <0.25 ppm apart."""
    from lucy_ng.detection.grouping import group_signals

    # Ibuprofen case: C4 at 44.90, C5 at 45.03 (0.13 ppm apart)
    peaks = [
        Peak1D(ppm=44.90, intensity=1.0, multiplicity="CH"),
        Peak1D(ppm=45.03, intensity=1.0, multiplicity="CH2"),
        Peak1D(ppm=129.38, intensity=2.0, multiplicity="CH"),
    ]

    result = group_signals(peaks, tolerance_ppm=0.25)

    assert len(result.groups) == 2
    group1 = [g for g in result.groups if 44.0 < g.mean_ppm < 46.0][0]
    assert len(group1.peaks) == 2  # 44.90 and 45.03 grouped
    assert 44.90 in [p.ppm for p in group1.peaks]
    assert 45.03 in [p.ppm for p in group1.peaks]
```

### CASE Validation Against Known Structure

```python
# tests/test_case_validation.py

@pytest.mark.slow
@pytest.mark.requires_database
def test_ibuprofen_case_with_detection(tmp_path):
    """Full CASE workflow on ibuprofen with v3.0 detection."""
    # Requires: database regenerated with v6 schema

    compound_dir = Path("data/nmrdata/active-lucy-ng-testprojects/CASE1")
    known_smiles = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"  # Ibuprofen

    # Run CASE agent (integration test, not unit test)
    result = run_case_agent(compound_dir)

    # Must-pass criteria
    assert result.status == "success"
    assert result.solutions_count > 0
    assert result.solutions_count < 100  # Detection constrains search space

    # Top 3 should include correct structure
    top_3_smiles = [s.smiles for s in result.ranked_solutions[:3]]
    assert any(is_same_structure(s, known_smiles) for s in top_3_smiles)

    # Prediction should be good for correct structure
    correct_solution = [s for s in result.ranked_solutions
                        if is_same_structure(s.smiles, known_smiles)][0]
    assert correct_solution.mae_ppm < 3.0
    assert correct_solution.matched_signals > 10  # Most signals matched
```

### Ranking Validation

```python
# tests/test_ranking_validation.py

def test_two_tier_ranking_prefers_complete_coverage():
    """Validate that complete signal coverage ranks higher than low MAE on subset."""
    from lucy_ng.ranking import rank_solutions

    # Solution A: 10/10 signals matched, MAE=3.5 ppm
    solution_a = RankedSolution(
        smiles="...",
        mae_ppm=3.5,
        matched_signals=10,
        total_signals=10,
    )

    # Solution B: 5/10 signals matched, MAE=1.2 ppm (coincidentally low)
    solution_b = RankedSolution(
        smiles="...",
        mae_ppm=1.2,
        matched_signals=5,
        total_signals=10,
    )

    ranked = rank_solutions([solution_a, solution_b])

    # Solution A should rank higher (complete coverage beats low MAE)
    assert ranked[0] == solution_a
    assert ranked[1] == solution_b
```

## State of the Art

### Sherlock CASE System Metrics

From Michael Wenk PhD thesis (2023):

| Metric | Sherlock Performance |
|--------|----------------------|
| Test cases solved | 40/45 (88.9%) |
| Correct at rank #1 | 38/40 (95%) |
| Mean prediction deviation | 0.83 ppm |
| Largest solved | Cucurbitacin E (C32H44O8, 40 heavy atoms) |
| Solution time | <2 seconds (median) |

**Key capabilities lucy-ng now has (v3.0):**
- Statistical hybridisation detection ✓
- Neighbourhood element constraints ✓
- Signal grouping with 0.25 ppm tolerance ✓
- Two-tier ranking (signal count + MAE) ✓
- Badlist filtering (3/4-membered rings) ✓
- HHB detection at formula level ✓

**Key capabilities lucy-ng still lacks:**
- Fragment library (24.5M SSCs) - deferred to v3.1+
- Combinatorial atom exchange in LSD - deferred to v3.1+
- Solvent-specific statistics - not planned
- COSY usage in agent workflow - identified gap from CASE3 test

### lucy-ng Performance Baseline

From v2.1 testing:

| Metric | v2.1 Performance |
|--------|------------------|
| Ibuprofen (CASE1) | Rank #1 but wrong structure (cyclohexadiene) |
| Solution count | 100s-1000s (unconstrained) |
| Agent iterations | 5-10 cycles typical |
| Prediction MAE | 2-5 ppm on correct structures |

**v3.0 expected improvements:**
- Solution count: <100 (detection constrains search space)
- Correct rank: Top 3 (statistical constraints guide)
- Agent iterations: 1-3 (fewer with better constraints)

## Open Questions

### Question 1: Database Regeneration Schedule

**What we know:**
- Regeneration takes 2-3 hours
- Must run before Tier 2 validation
- One-time blocker, not recurring

**What's unclear:**
- Should regeneration be part of Phase 40 or a separate action item?
- Can validation mark complete without it, or should it be a blocker?
- Who runs it (user, developer, automated CI)?

**Recommendation:**
- Include regeneration as Phase 40 Plan 1 (prerequisite task)
- Mark as "can run overnight" in plan notes
- Validation report documents "before/after regeneration" state

### Question 2: COSY Usage in Agent

**What we know:**
- Pulegone test revealed agent identifies COSY but doesn't use it
- COSY provides H-H connectivity, constrains CH2 positions in rings
- Absence caused wrong keto position in Pulegone structure

**What's unclear:**
- Is COSY usage a v3.0 requirement or v3.1 enhancement?
- Should Phase 40 validation include COSY workflow testing?
- Does agent need explicit COSY protocol in knowledge base?

**Recommendation:**
- Document as v3.0 gap in validation report
- Defer COSY agent integration to v3.1 (separate from statistical detection)
- Include in "future improvements" section of Phase 40 report

### Question 3: Validation Success Criteria

**What we know:**
- Ibuprofen must rank top 3 with v3.0 (fixes v2.1 failure)
- Detection commands must return sensible frequencies
- Solution space must reduce vs v2.1

**What's unclear:**
- What's the minimum number of test compounds for "validation complete"?
- Should metrics be quantitative (MAE < X) or qualitative (better than v2.1)?
- How to handle stochastic agent behavior (different ranks per run)?

**Recommendation:**
- Minimum 3 CASE tests (ibuprofen + pulegone + 1 simple)
- Qualitative success: correct structure in top 3, solution count <100
- Quantitative tracking: MAE, rank, iterations (but not hard thresholds)
- Document agent non-determinism as known limitation

## Sources

### Primary (HIGH confidence)

- State of the codebase:
  - `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/STATE.md` - v3.0 progress, blockers
  - `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/database/schema.py` - Schema v6 definition
  - Database schema query: `sqlite3 lucy-ng-derep.db "PRAGMA table_info(hose_stats)"`

- Test infrastructure:
  - 732 pytest functions across 42 files (grep count)
  - `/Users/steinbeck/Dropbox/develop/lucy-ng/tests/test_detection_*.py` - Detection test coverage

- Test data:
  - `/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/` - 9 test cases
  - CASE1 (Ibuprofen C13H18O2), CASE3 (Pulegone C10H16O) - Known formulas
  - CASE3 analysis findings from 2026-02-11 test run

### Secondary (MEDIUM confidence)

- Database regeneration estimates:
  - Phase 34-03 notes: "~2-3 hours" for full regeneration pass
  - `lucy database generate-hose-stats --help` - Command documentation
  - Input file: predicted_coconut.sdf (4.4 GB, 173M lines)

- Sherlock performance metrics:
  - `/Users/steinbeck/Dropbox/develop/lucy-ng/background/sherlock-analysis.md`
  - Original source: Michael Wenk PhD thesis (2023)

### Tertiary (LOW confidence)

- Agent execution time estimate (5-15 minutes per CASE): Inferred from user context, not measured
- nmrXiv download feasibility: Assumed based on Sherlock methodology, not verified

## Metadata

**Confidence breakdown:**
- Test infrastructure inventory: HIGH - Direct file system queries and pytest count
- Database blocker analysis: HIGH - Confirmed via SQLite queries showing empty detection columns
- Regeneration time estimate: MEDIUM - From Phase 34 notes, not independently measured
- Validation metrics: MEDIUM - Adapted from Sherlock analysis, not lucy-ng specific
- CASE test time estimate: LOW - Inferred, not measured

**Research date:** 2026-02-11
**Valid until:** 2026-03-11 (30 days - schema and infrastructure are stable)

**Key dependencies:**
- Database regeneration blocks Tier 2 validation
- COSY agent integration is a separate concern (v3.1 candidate)
- Phase 40 can partially complete with Tier 1 (unit tests) before database regen
