# Domain Pitfalls: Statistical 4J HMBC Detection

**Domain:** Database-backed 4J CH HMBC coupling detection for CASE pipeline
**Researched:** 2026-03-10
**Confidence:** MEDIUM-HIGH (WebCocon literature + codebase analysis + v4.0 UAT failure data + Sherlock thesis)

---

## Critical Pitfalls

Mistakes that silently produce wrong structures, corrupt statistics, or break the existing CASE pipeline.

### Pitfall 1: False Positives Are More Dangerous Than False Negatives

**What goes wrong:**
If the 4J detector incorrectly flags a real 3J HMBC correlation as "potential 4J," the lsd-engineer defers it. This removes a valid structural constraint from LSD, expanding the solution space and potentially allowing wrong structures that would have been excluded. The CASE run produces more solutions, lower-quality ranking, or misses the correct structure entirely — and the user has no obvious signal that the 4J detector caused the problem.

**Why it happens:**
Developers naturally focus on catching 4J couplings (the known failure mode from ibuprofen UAT), leading to aggressive thresholds. The asymmetry is subtle: a missed 4J (false negative) produces the same failure as having no detector at all — bad but understood. A false positive produces a *new* failure mode that did not exist before the detector was added.

**Consequences:**
- Regression: compounds that previously solved correctly now fail because valid constraints are deferred
- Hard to diagnose: "too many solutions" is a generic symptom with many causes
- Erodes trust in the detector, leading agents to ignore flagging entirely

**Prevention:**
1. **Conservative thresholds**: Start with high specificity (few false positives) even at cost of missing some 4J couplings. A 4J probability threshold of 15-20% is safer than 5%. The current v6.0 heuristic (aromatic CH to aliphatic C, 4+ aromatic carbons) is a reasonable conservative starting point — statistical detection should be strictly more precise, not less.
2. **"Flag, don't remove" architecture**: The v6.0 design already does this — 4J correlations are flagged for the lsd-engineer to defer, not automatically removed. Maintain this. The agent can choose to include flagged correlations if solution count is too high without them.
3. **Regression testing**: Before shipping, test on all 6 existing test compounds (Ibuprofen, PSP, MC047_9, Sali_Eth, 4-Hydroxy-3-Iodo-biphenyl, 4-(1-Hydroxyethyl)benzoic acid isopropylester). Any compound that produces MORE solutions or different ranking after adding 4J detection has a regression.
4. **Return probability, not binary flag**: Give the agent a probability (e.g., "12% of 4-bond paths in the database for this atom-type pair") so it can make informed decisions rather than trusting a hard cutoff.

**Detection:**
- Run existing test compounds through the detection CLI with and without 4J detection
- Compare flagged correlations against known ground truth for ibuprofen (exactly 3 should be flagged)
- If non-aromatic compounds get ANY correlations flagged, that is a false positive worth investigating

### Pitfall 2: Combinatorial Explosion When Too Many Correlations Are Deferred

**What goes wrong:**
The WebCocon paper (Junker et al., Molecules 2021) demonstrated that setting 4J-Flag to unlimited (-1) caused solution count to jump from 4 to 6,045 and computation time to increase 1000x. Lucy-ng's LSD backend has the same fundamental problem: each deferred HMBC correlation removes a structural constraint, expanding the search space exponentially. Ibuprofen had 3 genuine 4J correlations out of ~15 total HMBC — if the detector over-flags (say 8 of 15), the solution space explodes.

**Why it happens:**
Each HMBC correlation flagged as "potential 4J" is deferred by the lsd-engineer, effectively weakening the constraint set. With N deferred correlations, the problem becomes drastically under-constrained. The existing deferral protocol (v6.0 lsd-engineer) defers all flagged correlations to the last batch — if too many are flagged, the early batches lack sufficient constraints.

**Consequences:**
- LSD may timeout or produce thousands of solutions
- Ranking becomes meaningless with too many candidates
- Agent enters failure loop: "too many solutions -> add more constraints -> but constraints are deferred"

**Prevention:**
1. **Cap the number of deferred correlations**: Never defer more than 3-4 correlations simultaneously. If the detector flags more, only defer the highest-probability ones and include the rest as normal HMBC constraints.
2. **Iterative deferral**: If initial LSD run with all non-flagged constraints still yields too many solutions, the agent should un-defer the lowest-probability flagged correlations one at a time to add back constraints.
3. **Never modify LSD bond distance to 2-4**: Do NOT change HMBC from `min_bonds=2, max_bonds=3` to `min_bonds=2, max_bonds=4` in the LSD file. Instead, defer (exclude) the suspect correlation entirely. This is what the current agent design does — preserve this approach. The WebCocon paper proved that expanding bond distance causes 1000x computation increase.

**Detection:**
- Solution count > 100 after deferring flagged correlations = likely over-flagging
- More than 4 correlations flagged in a single compound = investigate false positives
- Compare solution count with 0 deferred vs N deferred; if ratio exceeds 10x, reduce N

### Pitfall 3: Atom-Type Classification Ambiguity From Shifts Alone

**What goes wrong:**
The 4J detector must classify atom types (aromatic CH, benzylic CH2, aliphatic CH, etc.) from only 13C chemical shifts and HSQC/DEPT multiplicities — the molecular structure is unknown. Chemical shift ranges overlap significantly between structural environments. A carbon at 128 ppm could be aromatic CH, vinyl CH, or even an allylic carbon in a strained system. A carbon at 45 ppm could be benzylic CH2, cyclopropane CH, or N-alpha CH.

**Why it happens:**
Chemical shift is a continuous variable influenced by many factors (substituent effects, ring current, solvent, temperature). The detector must bin shifts into categories to compute 4J probabilities, but any binning loses information at boundaries.

**Consequences:**
- Wrong atom-type assignment leads to looking up wrong 4J probability
- Aromatic/vinyl boundary (~110-130 ppm) is particularly problematic: vinyl CH has different 4J behavior than aromatic CH
- Aliphatic carbon near 50-60 ppm could be O-alpha (no 4J concern) or benzylic (high 4J concern)

**Prevention:**
1. **Use shift windows, not discrete categories**: Instead of classifying "128 ppm = aromatic CH," query the database with a shift window (e.g., 126-130 ppm) and let the statistical distribution of bond paths speak for itself. This is exactly what the existing detection infrastructure does for hybridisation/neighbours — follow the same pattern.
2. **Combine shift + multiplicity + hybridisation**: An sp2 CH at 128 ppm is much more likely aromatic than an sp3 CH2 at 128 ppm. Use all available evidence from the existing detection commands.
3. **Don't require explicit atom-type classification**: Instead of "aromatic CH paired with benzylic CH2 -> probability = X%," compute "for any C-H pair where C1 is at 128 ppm (sp2 CH) and C2 is at 45 ppm (sp3 CH2), what fraction of matching database pairs have shortest bond path = 4?" This avoids explicit atom-type bins entirely and follows the existing shift-window detection paradigm.

**Detection:**
- Unit tests with boundary cases: 110 ppm (aromatic vs vinyl), 55 ppm (benzylic vs O-alpha), 140 ppm (aromatic vs vinyl quaternary)
- Compare classification against known test compounds where structure is known

### Pitfall 4: Database Bias — Natural Products Skew Toward Aromatic Compounds

**What goes wrong:**
COCONUT is heavily biased toward natural products, which are disproportionately aromatic (flavonoids, alkaloids, phenylpropanoids). If 70% of database compounds are aromatic, the 4J statistics for aromatic motifs will have excellent statistical power but may be overly aggressive. Rare structural motifs (macrocycles, polyketides with few aromatics) will have unreliable statistics with few observations.

**Why it happens:**
The 928K compound database was built for dereplication and HOSE prediction, not for balanced structural diversity. No effort was made to ensure uniform representation of structural motifs.

**Consequences:**
- 4J probabilities for aromatic-benzylic pairs are statistically robust but may overgeneralize (treating all aromatic systems the same regardless of substitution pattern)
- 4J probabilities for non-aromatic motifs (vinyl-allylic, etc.) may have too few data points to be reliable
- Low-observation results (< 100 matching pairs) masquerade as confident statistics

**Prevention:**
1. **Report observation count alongside probability**: "4J probability = 12% (based on 45,000 compound pairs)" vs "4J probability = 8% (based on 47 compound pairs)." The agent can weight these differently.
2. **Set minimum observation threshold**: Below N observations (e.g., 50), return "insufficient data" rather than a probability. The existing detection system uses this pattern (hybridisation returns "No data available" when total_observations = 0).
3. **Aggregate across all compounds, not by formula**: Unlike HHB detection (which queries by exact formula), 4J statistics should aggregate across all compounds matching the shift/multiplicity criteria. Formula-specific filtering would destroy statistical power for this use case.

**Detection:**
- After database generation, check observation counts per shift-pair bin
- Any bin with < 50 observations should be flagged as low-confidence
- Compare total aromatic-pair observations vs non-aromatic-pair observations to quantify bias

---

## Moderate Pitfalls

### Pitfall 5: W-Pathway Geometry Cannot Be Inferred From Bond Distance Alone

**What goes wrong:**
Not all 4-bond coupling paths produce observable HMBC correlations. The W-pathway (planar zigzag arrangement of 4 bonds) produces couplings of 1-3 Hz, easily visible in HMBC. Non-W-pathway 4J couplings are typically < 0.5 Hz and invisible. The database stores bond-path distance (number of bonds), not coupling constant or dihedral geometry. A 4-bond path that would never produce an observable HMBC peak is indistinguishable from a W-pathway that always does.

**Why it happens:**
Bond-path distance is a graph property computed from the molecular graph (RDKit GetShortestPath/GetDistanceMatrix). Coupling constant magnitude depends on orbital overlap, which depends on 3D geometry. Computing coupling constants would require 3D structure optimization and DFT calculations — infeasible for 928K compounds.

**Consequences:**
- 4J probability will be inflated: many 4-bond paths exist that never produce HMBC peaks
- A "4J probability = 30%" might mean "30% of pairs are 4 bonds apart" but only "5% produce observable couplings"
- This reduces specificity: more false positives than the raw numbers suggest

**Prevention:**
1. **Acknowledge the limitation**: The detector flags *potential* 4J, not *confirmed* 4J. The probability represents "fraction of database pairs at this shift combination that are 4 bonds apart," which is an upper bound on observable 4J coupling probability. Document this clearly in the CLI output.
2. **Use aromatic substructure as proxy for W-pathway**: In aromatic systems, the W-pathway is geometrically guaranteed by ring planarity. If both carbons are in the same aromatic ring system (or one is aromatic and the other is benzylic), the W-pathway is likely. The existing `in_aromatic` column in hose_stats could help — if both HOSE codes have high in_aromatic frequency, the 4J path is more likely to produce observable coupling.
3. **Higher threshold for non-aromatic pairs**: For non-aromatic shift pairs (both carbons < 100 ppm or both > 160 ppm), use a higher flagging threshold (e.g., 25%) because the W-pathway probability is lower.

**Detection:**
- Compare flagging rate on aromatic vs non-aromatic test compounds
- If non-aromatic compounds get heavily flagged, the threshold needs adjustment

### Pitfall 6: Performance — Bond Path Computation at Database Scale

**What goes wrong:**
Computing shortest bond paths for all C-H pairs across 928K compounds is computationally expensive. Each compound has N carbon atoms and we need pairwise distances. With ~15 carbons per average natural product, that is ~105 pairs per compound (N*(N-1)/2) x 928K compounds = ~97M pair computations. This is feasible but requires attention to implementation.

**Why it happens:**
RDKit's GetDistanceMatrix (Floyd-Warshall, all-pairs shortest path in one call) is efficient per molecule, but 928K calls with molecule parsing, SMILES deserialization, and database writes add up. Based on HOSE stats generation timing (8h39m for 7.9M records with more complex per-atom processing), bond path generation is estimated at 2-4 hours.

**Consequences:**
- Database generation takes hours without checkpointing = restart risk
- Memory pressure from accumulating statistics before batch write
- Re-generation needed if schema changes, multiplying the cost

**Prevention:**
1. **Reuse checkpoint pattern**: The existing `operation_checkpoint` table and `iter_compounds_with_shifts_from` method handle resumable iteration. Use the exact same pattern as `stats_generator.py` which already solves this problem.
2. **Use GetDistanceMatrix, not GetShortestPath**: `Chem.GetDistanceMatrix(mol)` returns all-pairs shortest paths in one call. This is O(N^3) but much faster than N^2 individual BFS calls for typical molecule sizes (N < 50).
3. **Aggregate during generation**: Instead of storing per-compound per-pair results, aggregate into shift-pair bins during generation. A table like `(shift_bin_1, multiplicity_1, shift_bin_2, multiplicity_2, distance_4_count, total_count)` is much smaller than per-compound data.
4. **Test on 10K compounds first**: Measure per-compound cost and project total time before committing to full run. If estimated time exceeds 6 hours, optimize the inner loop before proceeding.

**Detection:**
- Test generation on first 10K compounds to estimate total time
- Monitor memory usage during generation (keep < 4 GB resident)
- Verify checkpoint recovery by killing process mid-run and restarting

### Pitfall 7: Schema Migration Complexity — Seventh Schema Version

**What goes wrong:**
The database is at schema v6 with migrations from v3->v4->v5->v6. Adding 4J statistics requires v7. Each migration adds complexity. If the 4J statistics design changes during development, you may need v7->v8 before the milestone ships.

**Why it happens:**
Iterative development naturally produces schema evolution. The existing migration chain works, but each new step must be backward-compatible and handle partial data.

**Consequences:**
- Schema change mid-milestone requires re-running multi-hour generation
- Users with existing databases must run migration without losing data
- Database download on Figshare must be updated

**Prevention:**
1. **New table, not new columns**: Add a `coupling_path_stats` table rather than extending `hose_stats` (which already has 17 columns). A separate table allows independent regeneration without touching HOSE stats.
2. **Design the schema before writing generation code**: Get the table structure right in Phase 1. Changing it after generation takes hours.
3. **Include version check in CLI**: `lucy database info` should report whether 4J stats are populated (table exists AND has rows), so the agent knows if the feature is available.
4. **Follow existing migration pattern exactly**: `migrate_v6_to_v7` should mirror the structure of `migrate_v5_to_v6` in schema.py.

**Detection:**
- Run migration on a copy of the production database before modifying original
- Verify all existing `lucy detect` commands still work after migration (hybridisation, neighbours, hhb, grouping)
- Check database size increase (estimate: 50-200 MB for the new table)

### Pitfall 8: Agent Behavior — Agents May Ignore or Misuse Statistical 4J Flags

**What goes wrong:**
v3.0 and v4.0 UAT both showed agents dropping constraints across iterations. Even with a perfect 4J detector, the lsd-engineer may forget to carry deferred_4j entries across iterations, the nmr-chemist may not run the new detection command, or the solution-analyst may not factor 4J status into quality assessment. The v6.0 heuristic 4J pipeline was added across 3 agents but has NEVER been tested in a live CASE run.

**Why it happens:**
Agent behavior is governed by natural language instructions in agent definition files (~300-1100 lines each). New features require adding instructions to multiple agents. The more complex the protocol, the higher the chance of agent error. The constraint inventory persistence mechanism (JSON in LSD headers) helps, but the agent must actually read and maintain it.

**Consequences:**
- 4J detection works perfectly in unit tests but agents don't use it correctly in practice
- Deferred correlations silently re-added in iteration 2 (same bug pattern as v3.0 badlist loss)
- Solution analyst ignores "includes 4J correlations" caveat when ranking

**Prevention:**
1. **End-to-end UAT is mandatory**: Unit tests for the detection command are necessary but not sufficient. The milestone must include a live CASE run on ibuprofen (known 4J compound) to verify the full pipeline works end-to-end.
2. **Constraint inventory persistence**: The deferred_4j field in the constraint inventory JSON (added in v6.0) is the key persistence mechanism. Verify it survives across iterations by checking the LSD file header in each iteration during UAT.
3. **Keep agent instructions simple**: "Run `lucy detect hmbc4j` and report results" is more reliable than a complex multi-step protocol. The CLI command should return clear, structured JSON output that the agent copies verbatim.
4. **Minimize agent changes**: The v6.0 agent modifications already established the 4J pipeline (flag in nmr-chemist, defer in lsd-engineer, verify in solution-analyst). The v7.0 change should be minimal: replace "heuristic 4J flagging" with "run `lucy detect hmbc4j`" in nmr-chemist. Do not redesign the pipeline.

**Detection:**
- Grep CASE-PROGRESS.md for "deferred_4j" across all iterations after UAT
- Compare iteration 1 deferred list with final iteration deferred list — they should match
- Check that flagged correlations match the CLI output (agent correctly transcribed the detection result)

---

## Minor Pitfalls

### Pitfall 9: Non-Aromatic 4J Couplings — Real But Rare in CASE Context

**What goes wrong:**
Vinyl-allylic 4J couplings (through C=C double bonds) and other non-aromatic 4J couplings exist and are documented in the NMR literature (Hans Reich's NMR resource documents allylic, propargylic, and allenic 4J patterns). A developer may over-engineer detection for these rare cases, adding complexity without improving CASE outcomes.

**Prevention:**
- Focus v7.0 on aromatic 4J detection. Non-aromatic 4J can be deferred.
- The database should still store all 4-bond path statistics (including non-aromatic), but the CLI command and agent instructions should focus on aromatic-related pairs.
- If non-aromatic 4J is observed in a future UAT failure, lower the threshold for specific motifs.

### Pitfall 10: Testing on Known Structures Only — Survivorship Bias

**What goes wrong:**
All test compounds have known structures, so we know which HMBC correlations are 4J. In real CASE use, the structure is unknown. Testing only on compounds where we know the answer does not validate the detector for truly unknown compounds.

**Prevention:**
1. **Diverse test set**: Test on compounds with different 4J patterns: para-disubstituted benzene (ibuprofen), ortho-disubstituted, fused aromatics, and non-aromatic compounds (negative controls).
2. **Blind testing**: Run CASE on sanitized compounds (structure removed via `/lucy-ng:sanitise`) and check if the detector correctly identifies problematic correlations before seeing the answer.
3. **Cross-validation**: Split the 928K database. Generate statistics on one half, validate predictions on the other.

### Pitfall 11: CLI Command Design — Input/Output Contract

**What goes wrong:**
The existing detection commands follow a consistent pattern: take shift values and/or formula, return JSON with `--format json`. A poorly designed 4J command that requires different input types (two shifts plus two multiplicities plus formula) or returns a different output structure will confuse both agents and developers.

**Prevention:**
- Follow existing CLI patterns exactly. Input: two carbon shifts + optional multiplicities. Output: JSON with probability, observation_count, recommendation, and source shifts.
- Naming: `lucy detect hmbc4j` fits the existing `lucy detect {hybridisation|neighbours|hhb}` pattern.
- Include a batch mode that takes all HMBC correlations at once (agents prefer a single command call over N individual calls).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Database schema design | Over-engineering or under-specifying table structure (Pitfall 7) | Design schema before generation code. New table, not column additions to hose_stats. |
| Statistics generation | Long runtime without checkpoints (Pitfall 6) | Reuse existing checkpoint pattern from stats_generator.py. Test on 10K compounds first. |
| Detection CLI command | Returning binary flag instead of probability (Pitfall 1) | Return probability + observation count + recommendation in JSON. |
| Threshold calibration | False positives from aggressive thresholds (Pitfalls 1, 2) | Start conservative (15-20%). Test on all 6 existing compounds. Cap deferrals at 3-4. |
| Agent integration | Agents not correctly using the new command (Pitfall 8) | Minimal agent changes — replace heuristic with CLI call. Keep JSON output structure simple. |
| UAT on ibuprofen | Only testing on known 4J compound (Pitfall 10) | Also test non-aromatic compounds as negative controls. |
| Atom-type inference | Misclassifying shift ranges (Pitfall 3) | Use shift windows + multiplicity, not discrete categories. Follow hybridisation detection pattern. |
| W-pathway detection | Conflating all 4-bond paths with observable 4J (Pitfall 5) | Use aromatic context as proxy. Higher threshold for non-aromatic pairs. |

---

## "Looks Done But Isn't" Checklist

- [ ] **Ibuprofen 4J detected**: `lucy detect hmbc4j` on ibuprofen HMBC data flags exactly the 3 known 4J correlations (C4a-C6, C5a-C7, plus the reverse)
- [ ] **No false positives on non-aromatic compounds**: Running detection on PSP, MC047_9, Sali_Eth produces 0 or near-0 flagged correlations
- [ ] **Observation counts reported**: Every probability comes with an observation count. Low counts (< 50) are marked as insufficient data.
- [ ] **Schema migration tested**: `migrate_v6_to_v7` runs on existing database without data loss. All existing `lucy detect` commands work unchanged.
- [ ] **Generation checkpointed**: Kill generation process mid-run, restart — continues from last checkpoint, final result identical to uninterrupted run.
- [ ] **Agent uses results**: Live CASE run on ibuprofen shows deferred_4j populated in constraint inventory, 4J correlations deferred from early batches, and correct aromatic structure found.
- [ ] **Cap enforced**: If > 4 correlations flagged, only top N are deferred. Agent does not defer all of them.
- [ ] **Regression-free**: All previously solvable test compounds still solve correctly with 4J detection enabled.

---

## Sources

### Literature
- [WebCocon 4J-HMBC Paper (Junker et al., Molecules 2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8398166/) — 4J-Flag causes 1000x computation increase, solution count from 4 to 6,045 when unrestricted. Optimal results when allowed 4J count matches actual 4J count.
- [Hans Reich NMR Data — Long-Range 4J Coupling](https://organicchemistrydata.org/hansreich/resources/nmr/?page=05-hmr-06-4j/) — Structural motifs for 4J: aromatic meta, allylic, propargylic, benzylic W-pathway couplings.
- [Columbia NMR — HSQC and HMBC](https://nmr.chem.columbia.edu/content/hsqc-and-hmbc) — No simple relationship between coupling constant magnitude and bond count.
- [i-HMBC (Nature Communications, 2023)](https://www.nature.com/articles/s41467-023-37289-z) — Isotope shift method to distinguish 2J from longer-range correlations at nanomole scale.

### Codebase
- `src/lucy_ng/detection/detector.py` — Existing StatisticalDetector with hybridisation, neighbours, hhb detection. Pattern to follow for 4J.
- `src/lucy_ng/detection/models.py` — Pydantic models for detection results. Template for 4J result model.
- `src/lucy_ng/prediction/stats_generator.py` — Checkpoint pattern, resumable generation, batch processing. Reuse for 4J stats generation.
- `src/lucy_ng/prediction/bond_pair_generator.py` — Bond pair generation pattern. Similar structure needed for coupling path generation.
- `src/lucy_ng/database/schema.py` — Schema v6, migration chain v3-v6. Follow pattern for v7 migration.
- `src/lucy_ng/lsd/generator.py` — LSD input generation with HMBC correlations at min_bonds=2, max_bonds=3.

### Agent Definitions (v6.0 Phase 56)
- `~/.claude/agents/lucy-nmr-chemist.md` — Heuristic 4J flagging (Section 3), [SETUP-COMPLETE] template with "Potential 4J correlations" field.
- `~/.claude/agents/lucy-lsd-engineer.md` — 4J Deferral Rule, deferred_4j in constraint inventory, 4J Batch (Final) protocol.
- `~/.claude/agents/lucy-solution-analyst.md` — Two-tier aromatic verification (Tier 1: warnings, Tier 2: prediction-based).

### Project Context
- `background/sherlock-analysis.md` — Sherlock also only supports manual 4J marking; no statistical detection exists in any published CASE system.
- MEMORY.md — v4.0 UAT: ibuprofen failure with 3 W-pathway 4J couplings, all 7 solutions lacked aromatic rings. v3.0 UAT: constraint loss across iterations.

---
*Pitfalls research for: Statistical 4J HMBC Detection (v7.0 milestone)*
*Researched: 2026-03-10*
