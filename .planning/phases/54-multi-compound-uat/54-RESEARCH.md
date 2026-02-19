# Phase 54: Multi-Compound UAT - Research

**Researched:** 2026-02-19
**Domain:** UAT validation of fragment library across multiple compounds
**Confidence:** HIGH

## Summary

Phase 54 is a User Acceptance Testing phase, not a code development phase. Its purpose is to validate the entire v5.0 fragment library pipeline (Phases 49-53) by running self-search recall tests and full CASE elucidation runs across multiple compounds, comparing solution counts with and without fragment injection.

The critical blocker is that the fragment database (`lucy-ng-fragments.db`) is currently populated with only 3,172 SSCs from a 100-compound sample. The full 928K-compound extraction has not been run and will take approximately 4 hours. Self-search recall on the 100-compound sample is 100%, confirming the pipeline works, but the fragment search results are meaningless with such a small library. The full extraction MUST complete before any CASE UAT runs can produce meaningful fragment results.

All 6 compounds in the `data/` directory are CASE-ready (13C + HSQC + HMBC minimum). However, ALL compounds are aromatic with benzylic substituents, meaning they all carry 4J HMBC coupling risk. Ibuprofen is a KNOWN 4J failure from v4.0 UAT. The UAT report must carefully distinguish 4J failures from fragment library gaps.

**Primary recommendation:** Run the full `lucy fragment build` extraction first (~4 hours), then execute self-search validation, then run CASE on all 6 compounds with and without fragment injection.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| VALD-01 | Multi-compound UAT on 5+ compounds with solution count before/after fragment injection | 6 CASE-ready compounds available locally, all with 13C + HSQC + HMBC. Full fragment DB extraction needed first (~4 hours). Agent integration confirmed in Phase 53. |
| VALD-02 | Self-search validation: 100 compounds' own spectra must find their own SSCs (>99% recall) | `lucy fragment build --sample 1000` with self-search validation built into CLI. 100-compound test showed 100% recall. Must re-run after full extraction to confirm at scale. |
</phase_requirements>

## Standard Stack

### Core (already implemented)
| Component | Version | Purpose | Status |
|-----------|---------|---------|--------|
| `lucy fragment build` | v5.0 | SSC extraction pipeline with checkpointing | Implemented, tested on 100-compound sample |
| `lucy fragment info` | v5.0 | Fragment DB statistics | Implemented, working |
| `lucy fragment search` | v5.0 | Bitset pre-screening + fine matching | Implemented, working |
| `lucy fragment to-lsd` | v5.0 | SMILES to DEFF/FEXP LSD file | Implemented, working |
| `/lucy-ng:case` | v4.0+ | Full CASE orchestrator with team agents | Implemented, fragment integration added in Phase 53 |
| `lucy lsd rank` | v3.0+ | Solution ranking with aromatic ring check | Implemented, working |

### Supporting (for UAT execution)
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `lucy fragment build --sample 1000` | Bin size validation with self-search recall | Before full extraction, verifies pipeline |
| `lucy fragment build data/reference/lucy-ng-derep.db` | Full 928K extraction | Before any meaningful CASE runs |
| `lucy fragment build --resume` | Resume interrupted extraction | If full build is interrupted |
| RDKit (`Chem.MolFromSmiles`) | Verify solution structures (aromatic ring check) | Post-CASE solution verification |

## Architecture Patterns

### UAT Execution Pattern

The UAT follows a sequential dependency chain:

```
1. Full Fragment Extraction (~4 hours)
   lucy fragment build data/reference/lucy-ng-derep.db --fresh

2. Self-Search Validation (built into sample mode)
   lucy fragment build data/reference/lucy-ng-derep.db --sample 1000
   (already validates recall on 100 compounds)

3. Per-Compound CASE Runs (2 runs each: with/without fragments)
   For each compound:
     a. Run CASE with fragment injection (default v5.0 behavior)
     b. Record solution count, rank, fragment usage
     c. Run CASE without fragment injection (disable DEFF/FEXP)
     d. Record baseline solution count
     e. Compare results

4. UAT Report Generation
   Aggregate results, identify 4J failures vs fragment gaps
```

### Compound Test Matrix

```
data/
 Ibuprofen/                 C13H18O2   15 heavy atoms  1 ring  4J KNOWN
 MC047_9/                   C10H14O2   12 heavy atoms  1 ring  4J risk
 PSP/                       C12H12O5   17 heavy atoms  1 ring  4J risk
 Sali_Eth/                  C18H20N2   20 heavy atoms  2 rings 4J risk
 4-Hydroxy-3-Iodo-biphenyl/ C12H9IO    14 heavy atoms  2 rings 4J risk + I
 4-(1-Hydroxyethyl).../     C12H16O3   15 heavy atoms  1 ring  4J risk
```

### NMR Data Inventory per Compound

| Compound | Formula | 13C | DEPT-135 | HSQC (edited) | HMBC | COSY | Notes |
|----------|---------|-----|----------|---------------|------|------|-------|
| Ibuprofen | C13H18O2 | /2 | /3 (dept135) | /6 (inv4gpqf) | /7 (inv4gplplrndqf) | /5 | Also DEPT-90 at /4 |
| MC047_9 | C10H14O2 | /2 | /3 (deptsp135) | /6 (hsqcedetgpsisp2.3) | /7 (hmbcetgpl3nd) | /5 | 2-hexyl-2H-pyran-6(3H)-one |
| PSP | C12H12O5 | /2 | -- | /6 (hsqcedetgpsisp) | /7 (hmbcetgpl3nd) | /5 | Mult from edited HSQC |
| Sali_Eth | C18H20N2 | /2 | -- | /6 (hsqcedetgpsisp) | /7 (hmbcetgpl3nd) | /5 | Largest (20 heavy atoms) |
| 4-Hydroxy-3-Iodo-biphenyl | C12H9IO | /2 | -- | /6 (hsqcedetgpsisp) | /7 (hmbcetgpl3nd) | /5 | Contains iodine; also NOESY at /8 |
| HEB (4-(1-Hydroxyethyl)benzoic acid isopropylester) | C12H16O3 | /2 | /13 (dept) | /5 (hsqcedetgpsisp2.3) | /4 (hmbcgplpndqf) | /8 | Note: non-standard exp numbering |

### Structure and Aromaticity Details

| Compound | SMILES | Aromatic atoms | Benzylic substituents | 4J risk |
|----------|--------|----------------|----------------------|---------|
| Ibuprofen | CC(C)Cc1ccc(C(C)C(=O)O)cc1 | 6 | YES (isobutyl + propionic) | HIGH (KNOWN failure) |
| MC047_9 | CCCCCc1cccc(=O)o1 | 6 | YES (pentyl chain) | HIGH |
| PSP | C=CC(=O)OCCOC(=O)c1ccccc1O | 6 | YES (ester chain) | HIGH |
| Sali_Eth | CCc1ccccc1/C=N/N=C/c1ccccc1CC | 12 | YES (ethyl + imine) | HIGH |
| 4-Hydroxy-3-Iodo-biphenyl | Oc1ccc(-c2ccccc2)cc1I | 12 | YES (biphenyl) | MEDIUM |
| HEB | CC(C)OC(=O)c1ccc(C(C)O)cc1 | 6 | YES (ester + hydroxyethyl) | HIGH |

### Anti-Patterns to Avoid

- **Running CASE without full fragment DB:** The 100-compound sample produces meaningless fragments (non-specific matches). Only the full 928K extraction produces a useful library.
- **Comparing compounds without baseline:** Every CASE run must be done TWICE (with and without fragments) to measure the fragment library's impact. Without baselines, no before/after comparison is possible.
- **Treating all failures as fragment gaps:** Many compounds will fail due to 4J HMBC couplings, which is a v4.0 known issue. The UAT report must distinguish between "4J caused failure" and "fragment library insufficient."
- **Running all compounds in parallel:** Each CASE run uses the team agent architecture which is resource-intensive. Run sequentially.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fragment extraction | Custom extraction script | `lucy fragment build` CLI | Pipeline has checkpointing, resume, self-search validation built in |
| Fragment search for CASE | Manual DEFF file creation | Agent integration from Phase 53 (lsd-engineer runs `lucy fragment search`) | Already integrated with zero-solution fallback |
| Solution comparison | Manual counting | `lucy lsd rank --format json` | Returns structured data with solution count, rank, MAE, aromatic ring flag |
| Self-search recall | Custom validation script | `lucy fragment build --sample N` (auto-validates when N >= 100) | Built into the CLI, prints recall percentage |

## Common Pitfalls

### Pitfall 1: Fragment DB Not Populated
**What goes wrong:** CASE runs find no fragments, or only nonsensical matches from the 100-compound sample.
**Why it happens:** Full extraction hasn't been run. Current DB has only 3,172 SSCs (should be ~24M).
**How to avoid:** Run `lucy fragment build data/reference/lucy-ng-derep.db --fresh` before any CASE testing. Verify with `lucy fragment info` that SSC count is in the millions.
**Warning signs:** `lucy fragment search` returns 0 fragments or fragments with unrelated SMILES.

### Pitfall 2: All Compounds Have 4J HMBC Risk
**What goes wrong:** Most or all CASE runs fail, making it appear the fragment library doesn't work, when the real cause is 4J HMBC exclusion.
**Why it happens:** All 6 local compounds are aromatic with benzylic substituents. This is the exact structural pattern that produces 4J couplings through aromatic rings.
**How to avoid:** The UAT report MUST check whether solutions lack aromatic rings (the `warnings` field in `lucy lsd rank` output). If solutions lack aromatic rings when 4+ carbons are in 110-160 ppm, that is a 4J indicator, not a fragment library problem.
**Warning signs:** Solutions with 5/7/9-membered rings instead of 6-membered aromatic rings; aromatic ring warnings in ranking output.

### Pitfall 3: Ibuprofen Expected to Fail
**What goes wrong:** Ibuprofen CASE run fails (correct structure not found), researcher panics.
**Why it happens:** This is a KNOWN v4.0 failure due to 3 W-pathway 4J HMBC couplings. Fragment injection cannot fix it because the 4J-constrained LSD file excludes the correct topology entirely.
**How to avoid:** Flag Ibuprofen as "expected 4J failure" in UAT report. The test is whether fragment injection still provides some benefit (reduce solution count even if all solutions are wrong).

### Pitfall 4: Extraction Takes Hours
**What goes wrong:** Full extraction is started during UAT session and takes ~4 hours, blocking progress.
**Why it happens:** 928K compounds * BFS fragmentation at radius 1-3 + ring environments = computationally intensive.
**How to avoid:** Start extraction as a background process or pre-run it before the UAT session. Use `--resume` if interrupted.
**Warning signs:** `tqdm` progress bar showing <100 compounds/sec (expect ~60 compounds/sec on M1 Mac).

### Pitfall 5: Comparing Wrong Metrics
**What goes wrong:** UAT focuses on whether correct structure is found (pass/fail) instead of solution count reduction.
**Why it happens:** Natural tendency to measure absolute success, but fragment library's purpose is to REDUCE solution counts, not guarantee correct structure.
**How to avoid:** Measure: (1) solution count without fragments, (2) solution count with fragments, (3) fragment conflict rate, (4) whether correct structure appears in top N. Report all four.

### Pitfall 6: Edited HSQC vs DEPT-135 Confusion
**What goes wrong:** Agent can't determine multiplicities for compounds without DEPT-135.
**Why it happens:** PSP, Sali_Eth, and 4-Hydroxy-3-Iodo-biphenyl lack standalone DEPT-135 but have multiplicity-edited HSQC (hsqcedetgpsisp).
**How to avoid:** The edited HSQC provides equivalent multiplicity information (CH positive, CH2 negative in the 2D). The CASE agent should handle this, but verify it works for compounds without DEPT-135.

### Pitfall 7: Non-Standard Experiment Numbering
**What goes wrong:** Agent assumes standard experiment numbering (1=1H, 2=13C, 3=DEPT, 5=COSY, 6=HSQC, 7=HMBC) but HEB uses different numbers.
**Why it happens:** HEB has HSQC at /5, HMBC at /4, COSY at /8, DEPT at /13 -- different from the typical layout.
**How to avoid:** The CASE agent reads pulse programs to auto-detect experiment types. Verify this works for HEB's non-standard numbering.

## Code Examples

### Running Full Fragment Extraction
```bash
# Start full extraction (background-safe with checkpointing)
lucy fragment build data/reference/lucy-ng-derep.db --fresh

# Expected output after ~4 hours:
# Compounds processed: ~928,000
# SSCs extracted: ~24,000,000 (estimated)
# Self-search recall validation not auto-run in full mode

# Verify
lucy fragment info data/reference/lucy-ng-fragments.db
# Expected: SSC count in millions, bin size 2.0 ppm
```

### Self-Search Validation
```bash
# Run sample build with auto-validation (100 compounds tested for recall)
lucy fragment build data/reference/lucy-ng-derep.db --sample 1000

# Expected output:
# Self-search recall: 100.0% (100/100)
# (or >99%)
```

### CASE Run with Fragment Injection (default v5.0 behavior)
```bash
# The CASE orchestrator spawns the team-based agent which now includes
# fragment search in the lsd-engineer workflow (Phase 53 integration).
# Run via the /lucy-ng:case sub-command for each compound.

# For Ibuprofen:
# /lucy-ng:case data/Ibuprofen C13H18O2

# Results appear in data/Ibuprofen/analysis/CASE-PROGRESS.md
# Each iteration logs: Fragment search, Fragment file, DEFF FEXP
```

### CASE Run WITHOUT Fragment Injection (baseline)
```bash
# To get baseline solution counts without fragments, one approach:
# 1. Temporarily rename/remove lucy-ng-fragments.db
# 2. Run CASE normally -- fragment search will fail gracefully
# 3. Record solution counts
# 4. Restore fragment DB

# Alternative: modify LSD file post-iteration to remove DEFF/FEXP lines
# and re-run LSD solver manually
```

### Checking Fragment Search for a Compound
```bash
# Test fragment search for MC047_9 shifts
lucy fragment search \
  --shifts "163.5,152.4,143.2,111.5,99.8,33.1,31.2,27.0,26.5,22.4" \
  --format json --top 3

# Check if results are meaningful (high atom count, low AVGDEV)
```

### Solution Comparison Metrics
```bash
# After CASE run, extract metrics:
lucy lsd rank solutions.smi --shifts "..." --format json

# Key fields in JSON output:
# - ranked_solutions: array of solutions
# - warnings: aromatic ring mismatch warning
# - Each solution: smiles, matched_count, mae, has_aromatic_ring
```

## State of the Art

| Aspect | Current State | Required for UAT |
|--------|---------------|------------------|
| Fragment DB | 3,172 SSCs (100 compounds) | Millions of SSCs (928K compounds) |
| Self-search recall | 100% on 100-compound sample | Verify >99% on full DB |
| Agent integration | lsd-engineer has fragment workflow (Phase 53) | Tested on Ibuprofen only |
| CASE pipeline | Working (v4.0 UAT confirmed) | Need 5+ compound runs |
| Aromatic ring check | Working in `lucy lsd rank` | Need to correlate with 4J diagnosis |

## Open Questions

1. **Will the full extraction produce ~24M SSCs as Sherlock reports?**
   - What we know: 100-compound sample yielded 3,172 SSCs (~32 SSCs/compound). At this rate, 928K compounds would yield ~29M SSCs, which is in the right ballpark.
   - What's unclear: Deduplication at scale may reduce the count significantly.
   - Recommendation: Run the full extraction and report actual numbers.

2. **Can CASE runs be done without fragment injection for baseline comparison?**
   - What we know: The lsd-engineer searches for fragments at every iteration. If `lucy-ng-fragments.db` doesn't exist, the search will fail.
   - What's unclear: Whether the agent handles the fragment search failure gracefully (continues without fragment) or halts.
   - Recommendation: Test by temporarily removing the fragment DB for baseline runs. Alternatively, document the "without fragment" solution count from the first CASE iteration before fragments are applied.

3. **Do all 6 compounds fail due to 4J HMBC, or do some succeed?**
   - What we know: Ibuprofen is a KNOWN failure. All 6 compounds are aromatic with benzylic substituents.
   - What's unclear: The actual 4J coupling probabilities vary by compound. Some may have weaker 4J couplings that don't appear in the HMBC spectrum.
   - Recommendation: Run all 6 and categorize results. If most fail with aromatic ring warnings, that confirms the 4J problem is widespread and v5.1 (4J detection) is essential.

4. **Is MC047_9 actually a pyranone (not a benzene)?**
   - What we know: The MOL file shows CCCCCc1cccc(=O)o1, which is 2-pentyl-4H-pyran-4-one (a lactone, not a classic benzene).
   - What's unclear: Whether the aromatic ring in this compound has the same 4J coupling characteristics as a substituted benzene.
   - Recommendation: MC047_9 may actually have LOWER 4J risk because the ring contains O and C=O, which changes coupling pathways. This could be one of the compounds that succeeds.

5. **How to run CASE without fragments for controlled comparison?**
   - What we know: Phase 53 integrated fragment search into the agent workflow.
   - What's unclear: The cleanest way to disable fragment injection for baseline runs.
   - Recommendation: Run two sets of CASE runs - first with fragment DB present, then with it renamed. Or: since the fragment search gracefully falls back when DB is missing, simply test with DB absent first, then present.

## Sources

### Primary (HIGH confidence)
- Local filesystem: `data/` directory inventory, compound MOL files, Bruker experiment parameters
- Local filesystem: `src/lucy_ng/cli/fragment.py` - CLI implementation
- Local filesystem: `src/lucy_ng/fragments/extractor.py` - SSCExtractor pipeline
- Local filesystem: `.planning/milestones/v5.0-ROADMAP.md` - Phase 54 requirements
- Local filesystem: `.planning/REQUIREMENTS.md` - VALD-01, VALD-02 definitions
- Local filesystem: `background/sherlock-analysis.md` - Sherlock comparison
- Live verification: `lucy fragment build --sample 100 --fresh` - confirmed 100% self-search recall
- Live verification: `lucy fragment info` - confirmed DB schema v7, 3,172 SSCs
- Live verification: `lucy lsd check` - LSD and outlsd both available

### Secondary (MEDIUM confidence)
- Local filesystem: `background/wenk-thesis.txt` - Sherlock test case reference (Table 10, Table 13)
- Local filesystem: `.planning/STATE.md` - v4.0 UAT findings on Ibuprofen 4J failure

### Tertiary (LOW confidence)
- 4J coupling risk assessment for non-Ibuprofen compounds (based on structural analysis, not experimental verification)
- Full extraction time estimate (~4 hours, based on 100-compound sample rate extrapolation)

## Metadata

**Confidence breakdown:**
- Available compounds: HIGH - directly verified from filesystem
- Fragment pipeline status: HIGH - live-tested build, search, info commands
- Self-search recall: HIGH - verified 100% on 100-compound sample
- 4J coupling risk: MEDIUM - structural analysis only, no experimental HMBC inspection
- Full extraction time: MEDIUM - extrapolated from sample, actual time may vary
- CASE agent behavior with fragments: MEDIUM - integrated in Phase 53 but not UAT-tested yet

**Research date:** 2026-02-19
**Valid until:** 2026-03-19 (stable -- no moving parts, all code is implemented)
